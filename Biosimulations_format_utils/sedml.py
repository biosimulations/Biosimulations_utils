""" Utilities for working with SED-ML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import libsedml
from xml.sax import saxutils


def gen_sedml(model_species, sim, model_filename, sim_filename, level=1, version=3):
    """ Encode a simulation experiment into SED-ML

    Args:
        model_species (:obj:`list` of :obj:`dict`): List of species in the model. Each species should have the key `id`
        sim (:obj:`dict`): Simulation experiment
        model_filename (:obj:`str`): Path to the model        
        sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
        level (:obj:`int`): SED-ML level
        version (:obj:`int`): SED-ML version
    """
    if sim['model']['format']['name'] == 'SBML':
        Generator = SbmlSedMlGenerator
    else:
        raise NotImplementedError('Model format {} is not supported'.format(sim['model']['format']['name']))

    return Generator().run(model_species, sim, model_filename, sim_filename, level=level, version=version)


class SedMlGenerator(object):
    """ Base class for SED-ML generator for each model format """

    def run(self, model_species, sim, model_filename, sim_filename, level=1, version=3):
        """
        Args:
            model_species (:obj:`list` of :obj:`dict`): List of species in the model. Each species should have the key `id`
            sim (:obj:`dict`): Simulation experiment
            model_filename (:obj:`str`): Path to the model        
            sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
            level (:obj:`int`): SED-ML level
            version (:obj:`int`): SED-ML version
        """
        if sim['format']['name'] != 'SED-ML' or sim['format']['version'] != 'L{}V{}'.format(level, version):
            raise ValueError('Format must be SED-ML L{}V{}'.format(level, version))

        doc = libsedml.SedDocument()
        self._call_sedml(doc, doc, 'setLevel', level)
        self._call_sedml(doc, doc, 'setVersion', version)

        # metadata
        notes = []

        if sim.get('id', None):
            notes.append({'label': 'Id', 'value': saxutils.escape(sim['id'])})

        if sim.get('name', None):
            notes.append({'label': 'Name', 'value': saxutils.escape(sim['name'])})

        if sim.get('authors', None):
            notes.append({'label': 'Author(s)', 'value': '<ul>{}</ul>'.format(''.join(
                '<li>{}</li>'.format(saxutils.escape(self._format_person_name(author))) for author in sim['authors']))})

        if sim.get('description', None):
            notes.append({'label': 'Description', 'value': saxutils.escape(sim['description'])})

        if sim.get('tags', None):
            notes.append({
                'label': 'Tags',
                'value': '<ul>{}</ul>'.format(''.join('<li>{}</li>'.format(saxutils.escape(tag)) for tag in sim['tags'])),
            })

        if sim.get('refs', None):
            notes.append({
                'label': 'References',
                'value': '<ul>{}</ul>'.format(''.join('<li>{}</li>'.format(self._format_reference(ref)) for ref in sim['refs'])),
            })

        if sim.get('license', None):
            notes.append({'label': 'License', 'value': saxutils.escape(sim['license'])})

        if notes:
            notes_xml = '<ul xmlns="http://www.w3.org/1999/xhtml">{}</ul>'.format(
                ''.join('<li>{}: {}</li>'.format(note['label'], note['value']) for note in notes if note['value']))
            self._call_sedml(doc, doc, 'setNotes', notes_xml)

        # model
        model_sedml = doc.createModel()
        self._call_sedml(doc, model_sedml, 'setId', 'model')
        self._call_sedml(doc, model_sedml, 'setSource', model_filename)
        if sim['model']['format']['name'] == 'SBML':
            self._call_sedml(doc, model_sedml, 'setLanguage', 'urn:sedml:sbml')
        else:
            raise NotImplementedError('Model format {} is not supported'.format(sim['model']['format']['name']))  # pragma: no cover

        # parameter changes
        for model_change in sim['modelParameterChanges']:
            model_change_sedml = model_sedml.createChangeAttribute()
            if sim['model']['format']['name'] == 'SBML':
                self._call_sedml(doc, model_change_sedml, 'setTarget',
                                 '/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id="{}"]/@value'.format(
                                     model_change['parameter']['id']))
            else:
                raise NotImplementedError('Model format {} is not supported'.format(sim['model']['format']['name']))  # pragma: no cover
            self._call_sedml(doc, model_change_sedml, 'setNewValue', str(model_change['value']))

        # simulation
        sim_sedml = doc.createUniformTimeCourse()
        self._call_sedml(doc, sim_sedml, 'setId', 'simulation')
        self._call_sedml(doc, sim_sedml, 'setInitialTime', sim['startTime'])
        self._call_sedml(doc, sim_sedml, 'setOutputStartTime', sim['startTime'])
        self._call_sedml(doc, sim_sedml, 'setOutputEndTime', sim['endTime'])
        self._call_sedml(doc, sim_sedml, 'setNumberOfPoints', sim['numTimePoints'])

        # simulation algorithm
        alg_sedml = sim_sedml.createAlgorithm()
        self._call_sedml(doc, alg_sedml, 'setKisaoID', sim['algorithm']['id'])

        # simulation algorithm parameters
        for param in sim['algorithmParameterChanges']:
            param_sedml = alg_sedml.createAlgorithmParameter()
            self._call_sedml(doc, param_sedml, 'setKisaoID', param['parameter']['kisaoId'])
            self._call_sedml(doc, param_sedml, 'setValue', str(param['value']))

        # create a task to simulate the model
        task_sedml = doc.createTask()
        self._call_sedml(doc, task_sedml, 'setId', 'task')
        self._call_sedml(doc, task_sedml, 'setModelReference', model_sedml.getId())
        self._call_sedml(doc, task_sedml, 'setSimulationReference', sim_sedml.getId())

        # create a report for the simulation predictions
        report_sedml = doc.createReport()
        self._call_sedml(doc, report_sedml, 'setId', 'report')
        self._call_sedml(doc, report_sedml, 'setName', 'report')

        # add the simulation time to the report
        data_gen_sedml = doc.createDataGenerator()
        self._call_sedml(doc, data_gen_sedml, 'setId', 'data_generator_time')
        self._call_sedml(doc, data_gen_sedml, 'setName', 'time')

        var_sedml = data_gen_sedml.createVariable()
        self._call_sedml(doc, var_sedml, 'setId', 'var_time')
        self._call_sedml(doc, var_sedml, 'setName', 'time')
        self._call_sedml(doc, var_sedml, 'setTaskReference', 'task')
        self._call_sedml(doc, var_sedml, 'setSymbol', 'urn:sedml:symbol:time')
        self._call_sedml(doc, data_gen_sedml, 'setMath', libsedml.parseFormula(var_sedml.getId()))

        dataset_sedml = report_sedml.createDataSet()
        self._call_sedml(doc, dataset_sedml, 'setId', 'dataset_time')
        self._call_sedml(doc, dataset_sedml, 'setLabel', 'time')
        self._call_sedml(doc, dataset_sedml, 'setDataReference', data_gen_sedml.getId())

        # add the simulation predictions to the report
        for species in model_species:
            data_gen_sedml = doc.createDataGenerator()
            self._call_sedml(doc, data_gen_sedml, 'setId', 'data_generator_{}'.format(species['id']))
            self._call_sedml(doc, data_gen_sedml, 'setName', species['id'])

            var_sedml = data_gen_sedml.createVariable()
            self._call_sedml(doc, var_sedml, 'setId', 'var_{}'.format(species['id']))
            self._call_sedml(doc, var_sedml, 'setName', species['id'])
            self._call_sedml(doc, var_sedml, 'setTaskReference', 'task')
            if sim['model']['format']['name'] == 'SBML':
                self._call_sedml(doc, var_sedml, 'setTarget',
                                 '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id="{}"]'.format(species['id']))
            else:
                raise NotImplementedError('Model format {} is not yet supported'.format(sim['model']['format']['name']))  # pragma: no cover
            self._call_sedml(doc, data_gen_sedml, 'setMath', libsedml.parseFormula(var_sedml.getId()))

            dataset_sedml = report_sedml.createDataSet()
            self._call_sedml(doc, dataset_sedml, 'setId', 'dataset_{}'.format(species['id']))
            self._call_sedml(doc, dataset_sedml, 'setLabel', species['id'])
            self._call_sedml(doc, dataset_sedml, 'setDataReference', data_gen_sedml.getId())

        # save the SED-ML to a file
        libsedml.writeSedML(doc, sim_filename)

    @staticmethod
    def _format_person_name(person):
        """ Format a person for a note in a SED-ML document

        Args:
            person (:obj:`dict`): dictionary with three keys `firstName`, `middleName`, and `lastName`

        Returns:
            :obj:`str`
        """
        names = []

        if person.get('firstName', None):
            names.append(person['firstName'])

        if person.get('middleName', None):
            names.append(person['middleName'])

        if person.get('lastName', None):
            names.append(person['lastName'])

        return ' '.join(names)

    @staticmethod
    def _format_reference(ref):
        """ Format a journal article for a note in a SED-ML document

        Args:
            ref (:obj:`dict`): dictionary with keys

                * `authors`
                * `title`
                * `journal`
                * `volume`
                * `pages`
                * `year`

        Returns:
            :obj:`str`
        """
        return '{}. {}. <i>{}</i> <b>{}</b>, {} ({})'.format(
            saxutils.escape(ref['authors']),
            saxutils.escape(ref['title']),
            saxutils.escape(ref['journal']),
            saxutils.escape(str(ref['volume'])),
            saxutils.escape(ref['pages']),
            saxutils.escape(str(ref['year'])))

    @staticmethod
    def _call_sedml(doc, obj, method_name, *args, **kwargs):
        """ Call a method of a SED-ML object and check if there's an error

        Args:
            doc (:obj:`libsedml.SedDocument`): SED-ML document
            obj (:obj:`object`): SED-ML object
            method_name (:obj:`str`): method name
            *args (:obj:`list`): positional arguments to the method
            **kwargs (:obj:`dict`, optional): keyword arguments to the method

        Returns:
            :obj:`int`: SED-ML return code
        """
        method = getattr(obj, method_name)
        return_val = method(*args, **kwargs)
        if return_val != 0:
            msgs = []
            for i_error in range(doc.getNumErrors()):
                msgs.append(str(doc.getError(i_error).getErrorId()))

            if msgs:
                msg = '\n  ' + '\n  '.join(msgs)
            else:
                msg = ''

            raise ValueError('SED-ML error: {}{}'.format(return_val, msg))
        return return_val


class SbmlSedMlGenerator(SedMlGenerator):
    """ Generator for SED-ML for SBML models """

    def run(self, model_species, sim, model_filename, sim_filename, level=1, version=3):
        """
        Args:
            model_species (:obj:`list` of :obj:`dict`): List of species in the model. Each species should have the key `id`
            sim (:obj:`dict`): Simulation experiment
            model_filename (:obj:`str`): Path to the model        
            sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
            level (:obj:`int`): SED-ML level
            version (:obj:`int`): SED-ML version
        """
        return super(SbmlSedMlGenerator, self).run(model_species, sim, model_filename, sim_filename, level=level, version=version)
