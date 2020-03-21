""" Utilities for working with SED-ML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc
import libsedml
from xml.sax import saxutils


def gen_sedml(model_species, sim, model_filename, sim_filename, level=1, version=3):
    """ Encode a simulation experiment into SED-ML

    Args:
        model_species (:obj:`list` of :obj:`dict`): List of species in the model. Each species should have the key `id`
        sim (:obj:`dict`): Simulation experiment
        model_filename (:obj:`str`): Path to the model definition
        sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
        level (:obj:`int`): SED-ML level
        version (:obj:`int`): SED-ML version
    """
    if sim['model']['format']['name'] == 'SBML':
        Generator = SbmlSedMlGenerator
    else:
        raise NotImplementedError('Model format {} is not supported'.format(sim['model']['format']['name']))

    return Generator().run(model_species, sim, model_filename, sim_filename, level=level, version=version)


class SedMlGenerator(abc.ABC):
    """ Base class for SED-ML generator for each model format """

    def run(self, model_species, sim, model_filename, sim_filename, level=1, version=3):
        """
        Args:
            model_species (:obj:`list` of :obj:`dict`): List of species in the model. Each species should have the key `id`
            sim (:obj:`dict`): Simulation experiment
            model_filename (:obj:`str`): Path to the model definition
            sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
            level (:obj:`int`): SED-ML level
            version (:obj:`int`): SED-ML version
        """
        if sim['format']['name'] != 'SED-ML' or sim['format']['version'] != 'L{}V{}'.format(level, version):
            raise ValueError('Format must be SED-ML L{}V{}'.format(level, version))

        doc_sed = self._create_doc(level, version)
        self._add_metadata_to_doc(sim, doc_sed)

        model_sed = self._add_model_to_doc(sim['model'], model_filename, doc_sed)
        self._add_parameter_changes_to_model(sim['modelParameterChanges'], doc_sed, model_sed)

        sim_sed = self._add_timecourse_sim_to_doc(sim, doc_sed)
        alg_sed = self._add_algorithm_to_sim(sim['algorithm'], doc_sed, sim_sed)
        self._add_param_changes_to_alg(sim['algorithmParameterChanges'], doc_sed, alg_sed)
        task_sed = self._add_sim_task_to_doc(doc_sed, model_sed, sim_sed)

        report_sed = self._add_report_to_doc(doc_sed)
        time_gen_sed = self._add_data_gen_to_doc('time', 'time', doc_sed)
        self._add_var_to_data_gen('time', 'time', 'urn:sedml:symbol:time', doc_sed, time_gen_sed, task_sed)
        self._add_data_set_to_report('time', 'time', doc_sed, report_sed, time_gen_sed)

        self._add_task_results_to_report(model_species, doc_sed, task_sed, report_sed)

        self._export_doc(doc_sed, sim_filename)

    def _create_doc(self, level, version):
        """ Create a SED document

        Args:
            level (:obj:`int`): SED-ML level
            version (:obj:`int`): SED-ML version

        Returns:
            :obj:`libsedml.SedDocument`: SED document
        """
        doc_sed = libsedml.SedDocument()
        self._call_libsedml_method(doc_sed, doc_sed, 'setLevel', level)
        self._call_libsedml_method(doc_sed, doc_sed, 'setVersion', version)
        return doc_sed

    def _add_metadata_to_doc(self, sim, doc_sed):
        """ Add the metadata about a simulation experiment to the notes of a SED document

        * Id
        * Name
        * Authors        
        * Description
        * Tags
        * References
        * License

        Args:
            sim (:obj:`dict`): simulation experiment
            doc_sed (:obj:`libsedml.SedDocument`): SED document
        """
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
            self._call_libsedml_method(doc_sed, doc_sed, 'setNotes', notes_xml)

    def _add_model_to_doc(self, model, filename, doc_sed):
        """ Add a model to a SED document

        Args:
            model (:obj:`dict`): model
            model_filename (:obj:`str`): path to the model definition
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedModel`: SED model
        """
        model_sed = doc_sed.createModel()
        self._call_libsedml_method(doc_sed, model_sed, 'setId', 'model')
        self._call_libsedml_method(doc_sed, model_sed, 'setSource', filename)
        self._add_language_to_model(doc_sed, model_sed)
        return model_sed

    @abc.abstractmethod
    def _add_language_to_model(self, doc_sed, model_sed):
        """ Add a model language to a SED model

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model
        """
        pass  # pragma: no cover

    def _add_parameter_changes_to_model(self, changes, doc_sed, model_sed):
        """ Add model parameter changes to a SED document

        Args:
            changes (:obj:`list` of :obj:`dict`): model parameter changes
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model

        Returns:
            :obj:`list` of :obj:`libsedml.SedChangeAttribute`: list of SED model parameter changes
        """
        changes_sed = []
        for change in changes:
            changes_sed.append(self._add_parameter_change_to_model(change, doc_sed, model_sed))
        return changes_sed

    @abc.abstractmethod
    def _add_parameter_change_to_model(self, change, doc_sed, model_sed):
        """ Add a model parameter change to a SED document

        Args:
            change (:obj:`dict`): model parameter change
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model

        Returns:
            :obj:`libsedml.SedChangeAttribute`: SED model parameter change
        """
        pass  # pragma: no cover

    def _add_timecourse_sim_to_doc(self, sim, doc_sed):
        """ Add a timecourse simulation to a SED document

        Args:
            sim (:obj:`object`): simulation experiment
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedUniformTimeCourse`: timecourse simulation
        """
        sim_sed = doc_sed.createUniformTimeCourse()
        self._call_libsedml_method(doc_sed, sim_sed, 'setId', 'simulation')
        self._call_libsedml_method(doc_sed, sim_sed, 'setInitialTime', sim['startTime'])
        self._call_libsedml_method(doc_sed, sim_sed, 'setOutputStartTime', sim['startTime'])
        self._call_libsedml_method(doc_sed, sim_sed, 'setOutputEndTime', sim['endTime'])
        self._call_libsedml_method(doc_sed, sim_sed, 'setNumberOfPoints', sim['numTimePoints'])
        return sim_sed

    def _add_algorithm_to_sim(self, algorithm, doc_sed, sim_sed):
        """ Add a simulation algorithm to a SED document

        Args:
            algorithm (:obj:`dict`): simulation algorithm
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation

        Returns:
            :obj:`libsedml.SedAlgorithm`: SED simulation algorithm
        """
        alg_sed = sim_sed.createAlgorithm()
        self._call_libsedml_method(doc_sed, alg_sed, 'setKisaoID', algorithm['id'])
        return alg_sed

    def _add_param_changes_to_alg(self, changes, doc_sed, alg_sed):
        """ Add simulation algorithm parameter changes to a SED document

        Args:
            changes (:obj:`list` of :obj:`dict`): simulation algorithm parameter changes
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            alg_sed (:obj:`libsedml.SedAlgorithm`): SED simulation algorithm

        Returns:
            :obj:`list` of :obj:`libsedml.SedAlgorithmParameter`: list of SED simulation algorithm 
                paremeter changes
        """
        changes_sed = []
        for change in changes:
            changes_sed.append(self._add_param_change_to_alg(change, doc_sed, alg_sed))
        return changes_sed

    def _add_param_change_to_alg(self, change, doc_sed, alg_sed):
        """ Add simulation algorithm parameter change to a SED document

        Args:
            change (:obj:`dict`): simulation algorithm parameter change
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            alg_sed (:obj:`libsedml.SedAlgorithm`): SED simulation algorithm

        Returns:
            :obj:`libsedml.SedAlgorithmParameter`: SED simulation algorithm paremeter change
        """
        change_sed = alg_sed.createAlgorithmParameter()
        self._call_libsedml_method(doc_sed, change_sed, 'setKisaoID', change['parameter']['kisaoId'])
        self._call_libsedml_method(doc_sed, change_sed, 'setValue', str(change['value']))
        return change_sed

    def _add_sim_task_to_doc(self, doc_sed, model_sed, sim_sed):
        """ Add a task to simulate a model to a SED document

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation

        Returns:
            :obj:`libsedml.SedTask`: SED task
        """
        task_sed = doc_sed.createTask()
        self._call_libsedml_method(doc_sed, task_sed, 'setId', 'task')
        self._call_libsedml_method(doc_sed, task_sed, 'setModelReference', model_sed.getId())
        self._call_libsedml_method(doc_sed, task_sed, 'setSimulationReference', sim_sed.getId())
        return task_sed

    def _add_report_to_doc(self, doc_sed):
        """ Add a report to a SED document

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedReport`: SED report
        """
        report_sed = doc_sed.createReport()
        self._call_libsedml_method(doc_sed, report_sed, 'setId', 'report')
        self._call_libsedml_method(doc_sed, report_sed, 'setName', 'report')
        return report_sed

    def _add_data_gen_to_doc(self, id, name, doc_sed):
        """ Add a data generator to a SED document

        Args:
            id (:obj:`str`): id
            name (:obj:`str`): name
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedDataGenerator`: SED data generator
        """
        data_gen_sed = doc_sed.createDataGenerator()
        self._call_libsedml_method(doc_sed, data_gen_sed, 'setId', 'data_generator_' + id)
        self._call_libsedml_method(doc_sed, data_gen_sed, 'setName', 'time')
        return data_gen_sed

    def _add_var_to_data_gen(self, id, name, symbol, doc_sed, data_gen_sed, task_sed):
        """ Add a variable to a SED data generator

        Args:
            id (:obj:`str`): id
            name (:obj:`str`): name
            symbol (:obj:`str`): symbol
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            data_gen_sed (:obj:`libsedml.SedDataGenerator`): SED data generator
            task_sed (:obj:`libsedml.SedTask`): SED task

        Returns:
            :obj:`libsedml.SedVariable`: SED variable
        """
        var_sed = data_gen_sed.createVariable()
        self._call_libsedml_method(doc_sed, var_sed, 'setId', 'var_' + id)
        self._call_libsedml_method(doc_sed, var_sed, 'setName', name)
        self._call_libsedml_method(doc_sed, var_sed, 'setTaskReference', task_sed.getId())
        if symbol:
            self._call_libsedml_method(doc_sed, var_sed, 'setSymbol', symbol)
        self._call_libsedml_method(doc_sed, data_gen_sed, 'setMath', libsedml.parseFormula(var_sed.getId()))
        return var_sed

    def _add_data_set_to_report(self, id, name, doc_sed, report_sed, data_gen_sed):
        """ Add a dataset to a SED report

        Args:
            id (:obj:`str`): id
            name (:obj:`str`): name
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            report_sed (:obj:`libsedml.SedReport`): SED report
            data_gen_sed (:obj:`libsedml.SedDataGenerator): SED data generator

        Returns:
            :obj:`libsedml.SedDataSet`: SED data set
        """
        dataset_sed = report_sed.createDataSet()
        self._call_libsedml_method(doc_sed, dataset_sed, 'setId', 'dataset_' + id)
        self._call_libsedml_method(doc_sed, dataset_sed, 'setLabel', name)
        self._call_libsedml_method(doc_sed, dataset_sed, 'setDataReference', data_gen_sed.getId())
        return dataset_sed

    def _add_task_results_to_report(self, species, doc_sed, task_sed, report_sed):
        """ Add simulation predictions to a SED report

        Args:
            species (:obj:`list` of :obj:`dict`): species predicted by a model
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            task_sed (:obj:`libsedml.SedTask`): SED task
            report_sed (:obj:`libsedml.SedReport`): SED report

        Returns:
            :obj:`list` of :obj:`dict`: list of dictionary of data generators and variables for each
                simulation prediction
        """
        seds = []
        for spec in species:
            id = spec['id']
            data_gen_sed = self._add_data_gen_to_doc(id, id, doc_sed)
            var_sed = self._add_var_to_data_gen(id, id, None, doc_sed, data_gen_sed, task_sed)
            self._set_var_target(id, doc_sed, var_sed)
            self._add_data_set_to_report(id, id, doc_sed, report_sed, data_gen_sed)
            seds.append({
                'data_gen': data_gen_sed,
                'var': var_sed,
            })
        return seds

    @abc.abstractmethod
    def _set_var_target(self, id, doc_sed, var_sed):
        """ Set the target of a SED variable

        Args:
            id (:obj:`str`): id
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            var_sed (:obj:`libsedml.SedVariable`): SED: variable
        """
        pass  # pragma: no cover

    def _export_doc(self, doc_sed, filename):
        """ Export a SED document to an XML file

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            filename (:obj:`str`): path to save document in XML format
        """
        # save the SED document to a file
        libsedml.writeSedML(doc_sed, filename)

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
        """ Format a journal article for a note in a SED document

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
    def _call_libsedml_method(doc_sed, obj_sed, method_name, *args, **kwargs):
        """ Call a method of a SED object and check if there's an error

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            obj_sed (:obj:`libsedml.SedBase`): SED object
            method_name (:obj:`str`): method name
            *args (:obj:`list`): positional arguments to the method
            **kwargs (:obj:`dict`, optional): keyword arguments to the method

        Returns:
            :obj:`int`: libsedml return code
        """
        method = getattr(obj_sed, method_name)
        return_val = method(*args, **kwargs)
        if return_val != 0:
            msgs = []
            for i_error in range(doc_sed.getNumErrors()):
                msgs.append(str(doc_sed.getError(i_error).getErrorId()))

            if msgs:
                msg = '\n  ' + '\n  '.join(msgs)
            else:
                msg = ''

            raise ValueError('libsedml error: {}{}'.format(return_val, msg))
        return return_val


class SbmlSedMlGenerator(SedMlGenerator):
    """ Generator for SED-ML for SBML models """

    def _add_language_to_model(self, doc_sed, model_sed):
        """ Add a model language to a SED model

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model
        """
        self._call_libsedml_method(doc_sed, model_sed, 'setLanguage', 'urn:sedml:sbml')

    def _add_parameter_change_to_model(self, change, doc_sed, model_sed):
        """ Add a model parameter change to a SED document

        Args:
            change (:obj:`dict`): model parameter change
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model

        Returns:
            :obj:`libsedml.SedChangeAttribute`: SED model parameter change
        """
        change_sed = model_sed.createChangeAttribute()
        self._call_libsedml_method(doc_sed, change_sed, 'setTarget',
                                   '/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id="{}"]/@value'.format(
                                       change['parameter']['id']))
        self._call_libsedml_method(doc_sed, change_sed, 'setNewValue', str(change['value']))
        return change_sed

    def _set_var_target(self, id, doc_sed, var_sed):
        """ Set the target of a SED variable

        Args:
            id (:obj:`str`): id
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            var_sed (:obj:`libsedml.SedVariable`): SED: variable
        """
        self._call_libsedml_method(doc_sed, var_sed, 'setTarget',
                                   '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id="{}"]'.format(id))
