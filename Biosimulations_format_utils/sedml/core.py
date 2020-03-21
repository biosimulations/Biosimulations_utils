""" Utilities for working with SED-ML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from xml.sax import saxutils
import abc
import libsedml

__all__ = [
    'write_sedml',
    'read_sedml',
    'SedMlWriter',
    'SedMlReader',
]


def write_sedml(model_species, sim, model_filename, sim_filename, level=1, version=3):
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
        from .sbml import SbmlSedMlWriter
        Writer = SbmlSedMlWriter
    else:
        raise NotImplementedError('Model format {} is not supported'.format(sim['model']['format']['name']))

    return Writer().run(model_species, sim, model_filename, sim_filename, level=level, version=version)


class SedMlWriter(abc.ABC):
    """ Base class for SED-ML generator for each model format """

    LANGUAGE = None

    def run(self, model_species, sim, model_filename, sim_filename, level=1, version=3):
        """
        Args:
            model_species (:obj:`list` of :obj:`dict`): List of species in the model. Each species should have the key `id`
            sim (:obj:`dict`): Simulation experiment
            model_filename (:obj:`str`): Path to the model definition
            sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
            level (:obj:`int`): SED-ML level
            version (:obj:`int`): SED-ML version

        Returns:
            :obj:`libsedml.SedDocument`: SED document
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

        return doc_sed

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
        props = {}

        if sim.get('id', None):
            props['id'] = sim['id']

        if sim.get('name', None):
            props['name'] = sim['name']

        # if sim.get('authors', None):
        #    notes.append({'label': 'Author(s)', 'value': '<ul>{}</ul>'.format(''.join(
        #        '<li>{}</li>'.format(saxutils.escape(self._format_person_name(author))) for author in sim['authors']))})

        if sim.get('description', None):
            props['description'] = sim['description']

        # if sim.get('tags', None):
        #    notes.append({
        #        'label': 'Tags',
        #        'value': '<ul>{}</ul>'.format(''.join('<li>{}</li>'.format(saxutils.escape(tag)) for tag in sim['tags'])),
        #    })

        # if sim.get('refs', None):
        #    notes.append({
        #        'label': 'References',
        #        'value': '<ul>{}</ul>'.format(''.join('<li>{}</li>'.format(self._format_reference(ref)) for ref in sim['refs'])),
        #    })

        if sim.get('license', None):
            props['license'] = sim['license']

        # if notes:
        #    notes_xml = '<ul xmlns="http://www.w3.org/1999/xhtml">{}</ul>'.format(
        #        ''.join('<li>{}: {}</li>'.format(note['label'], note['value']) for note in notes if note['value']))
        #    self._call_libsedml_method(doc_sed, doc_sed, 'setAnnotation', notes_xml)

        self._add_annotation_to_obj(props, doc_sed, doc_sed)

    def _add_model_to_doc(self, model, filename, doc_sed):
        """ Add a model to a SED document

        Args:
            model (:obj:`dict`): model
            filename (:obj:`str`): path to the model definition
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedModel`: SED model
        """
        model_sed = doc_sed.createModel()
        self._call_libsedml_method(doc_sed, model_sed, 'setId', 'model')
        self._call_libsedml_method(doc_sed, model_sed, 'setSource', filename)
        self._call_libsedml_method(doc_sed, model_sed, 'setLanguage', self.LANGUAGE)
        return model_sed

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
        self._add_annotation_to_obj({'name': algorithm['name']}, doc_sed, alg_sed)
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
        self._add_annotation_to_obj({'name': change['parameter']['name']}, doc_sed, change_sed)
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
        self._call_libsedml_method(doc_sed, data_gen_sed, 'setId', 'data_gen_' + id)
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

    def _add_annotation_to_obj(self, annot, doc_sed, obj_sed):
        """ Add annotation to a SED object

        Args:
            annot (:obj:`object`): annotation
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            obj_sed (:obj:`libsedml.SedBase`): SED object
        """
        annot_xml = self._encode_obj_to_xml(annot)
        self._call_libsedml_method(doc_sed, obj_sed, 'setAnnotation',
                                   ('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
                                    '{}'
                                    '</rdf:RDF>').format(''.join(annot_xml)))

    def _encode_obj_to_xml(self, obj, id=None):
        """Encode an object into XML

        Args:
            obj (:obj:`object`): object

        Returns:
            :obj:`str`: XML representation of object
        """
        if isinstance(obj, dict):
            els_xml = []
            for key, val in obj.items():
                els_xml.append(self._encode_obj_to_xml(val, id=key))
            return '<rdf:Description>{}</rdf:Description>'.format(''.join(els_xml))
        elif isinstance(obj, set):
            els_xml = []
            for el in obj:
                els_xml.append("<rdf:li>" + self._encode_obj_to_xml(el) + "</rdf:li>")
            return '<rdf:Bag>{}</rdf:Bag>'.format(''.join(els_xml))
        elif isinstance(obj, list):
            for el in obj:
                els_xml.append("<rdf:li>" + self._encode_obj_to_xml(el) + "</rdf:li>")
            return '<rdf:Seq>{}</rdf:Seq>'.format(''.join(els_xml))
        else:
            if isinstance(obj, str):
                datatype = 'string'
            elif isinstance(obj, int):
                datatype = 'integer'
            elif isinstance(obj, float):
                datatype = 'float'
            else:
                raise ValueError('Value must be a float, integer, string, dist, or list not {}'.format(
                    obj._class__.__name__))
            return ('<rdf:value'
                    '{}'
                    ' rdf:datatype="http://www.w3.org/2001/XMLSchema#{}">'
                    '{}'
                    '</rdf:value>').format(' rdf:ID="{}"'.format(id) if id else '', datatype, obj)

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


def read_sedml(filename):
    """ Read a simulation experiment from a SED-ML document

    Args:
        filename (:obj:`str`): path to SED-ML document that describes a simulation experiment

    Returns:
        :obj:`list` of :obj:`dict`: List of species in the model. Each species should have the key `id`
        :obj:`dict`: Simulation experiment
        :obj:`str`: Path to the model definition
        :obj:`int`: SED-ML level
        :obj:`int`: SED-ML version
    """
    from .sbml import SbmlSedMlReader

    doc_sed = libsedml.readSedMLFromFile(filename)
    assert doc_sed.getNumModels() == 1, "SED-ML document must have one model"
    model_sed = doc_sed.getModel(0)
    model_lang = model_sed.getLanguage()

    if model_lang == SbmlSedMlReader.LANGUAGE:
        Reader = SbmlSedMlReader
    else:
        raise NotImplementedError('Model format {} is not supported'.format(model_format))

    return Reader().run(doc_sed)


class SedMlReader(abc.ABC):
    def run(self, doc_sed):
        """ Base class for reading a simulation experiment from a SED document

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`list` of :obj:`dict`: List of species in the model. Each species should have the key `id`
            :obj:`dict`: Simulation experiment
            :obj:`str`: Path to the model definition
            :obj:`int`: SED-ML level
            :obj:`int`: SED-ML version
        """
        sim = None

        assert doc_sed.getNumModels() == 1, "SED-ML document must have one model"
        model_sed = doc_sed.getModel(0)

        assert doc_sed.getNumTasks() == 1, "SED-ML document must have one task"
        task_sed = doc_sed.getTask(0)

        assert doc_sed.getNumSimulations() == 1, "SED-ML document must have one simulation"
        sim_sed = doc_sed.getSimulation(0)

        # model species
        model_species = []
        for i_data_gen in range(doc_sed.getNumDataGenerators()):
            data_gen_sed = doc_sed.getDataGenerator(i_data_gen)
            data_gen_id = data_gen_sed.getId()
            assert data_gen_id.startswith('data_gen_'), "Data generator id must start with `data_gen_`"
            species_id = data_gen_id[len('data_gen_'):]
            if species_id != 'time':
                model_species.append({
                    'id': species_id
                })

        # initialize simulation experiment with metadata
        sim = self._get_obj_annotation(doc_sed)

        # model parameter changes
        sim['modelParameterChanges'] = []
        for i_change in range(model_sed.getNumChanges()):
            change_sed = model_sed.getChange(i_change)
            assert isinstance(change_sed, libsedml.SedChangeAttribute), \
                "Changes must be attribute changes"
            change = self._get_parameter_change_from_model(change_sed)
            sim['modelParameterChanges'].append(change)

        # simulation timecourse
        sim['startTime'] = float(sim_sed.getInitialTime())
        assert float(sim_sed.getOutputStartTime()) == sim['startTime'], \
            "Simulation initial time and output start time must be equal"
        sim['endTime'] = float(sim_sed.getOutputEndTime())
        sim['length'] = sim['endTime'] - sim['startTime']
        sim['numTimePoints'] = int(sim_sed.getNumberOfPoints())

        # simulation algorithm
        alg_sed = sim_sed.getAlgorithm()
        alg_props = self._get_obj_annotation(alg_sed)
        sim['algorithm'] = {
            'id': alg_sed.getKisaoID(),
            'name': alg_props.get('name', None),
        }

        # simulation algorithm parameters
        sim['algorithmParameterChanges'] = []
        for i_change in range(alg_sed.getNumAlgorithmParameters()):
            change_sed = alg_sed.getAlgorithmParameter(i_change)
            change_props = self._get_obj_annotation(change_sed)
            sim['algorithmParameterChanges'].append({
                'parameter': {
                    'kisaoId': change_sed.getKisaoID(),
                    'name': change_props.get('name'),
                },
                'value': float(change_sed.getValue()),
            })

        # model filename
        model_filename = model_sed.getSource()

        # level and version
        level = doc_sed.getLevel()
        version = doc_sed.getVersion()

        # return simulation experiment
        return (model_species, sim, model_filename, level, version)

    def _get_obj_annotation(self, obj_sed):
        """ Get the annotated properies of a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object

        Returns:
            :obj:`dict`: dictionary of annotated properties and their values
        """
        annotations_xml = obj_sed.getAnnotation()
        assert annotations_xml.getNumChildren() <= 1
        if annotations_xml.getNumChildren() == 0:
            return {}

        annotation_xml = annotations_xml.getChild(0)
        if annotation_xml.getPrefix() != 'rdf' or annotation_xml.getName() != 'RDF':
            raise ValueError('Unable to decode XML')

        assert annotation_xml.getNumChildren() <= 1
        if annotation_xml.getNumChildren() == 0:
            return {}

        description_xml = annotation_xml.getChild(0)
        if description_xml.getPrefix() != 'rdf' or description_xml.getName() != 'Description':
            raise ValueError('Unable to decode XML')

        return self._decode_obj_from_xml(description_xml)

    def _decode_obj_from_xml(self, obj_xml):
        """ Decode an object from its XML representation

        Args:
            obj_xml (:obj:`libsedml.XMLNode`): XML representation of an object

        Returns:
            :obj:`object`: object
        """
        if obj_xml.getPrefix() != 'rdf':
            raise ValueError('Unable to decode object')

        if obj_xml.getName() == 'Description':
            val = {}
            for i_child in range(obj_xml.getNumChildren()):
                child_xml = obj_xml.getChild(i_child)

                id = None
                for i_attr in range(child_xml.getAttributesLength()):
                    if child_xml.getAttrPrefix(i_attr) == 'rdf' and child_xml.getAttrName(i_attr) == 'ID':
                        id = child_xml.getAttrValue(i_attr)
                        break

                if id is None:
                    raise ValueError('Unable to decode object')

                val[id] = self._decode_obj_from_xml(child_xml)
            return val

        if obj_xml.getName() == 'Bag':
            val = set()
            for i_child in range(obj_xml.getNumChildren()):
                child_xml = obj_xml.getChild(i_child)
                assert child_xml.getPrefix() == 'rdf' and child_xml.getName() == 'li'
                assert child_xml.getNumChildren() == 1
                val.add(self._decode_obj_from_xml(child_xml.getChild(0)))
            return val

        elif obj_xml.getName() == 'Seq':
            val = []
            for i_child in range(obj_xml.getNumChildren()):
                child_xml = obj_xml.getChild(i_child)
                assert child_xml.getPrefix() == 'rdf' and child_xml.getName() == 'li'
                assert child_xml.getNumChildren() == 1
                val.append(self._decode_obj_from_xml(child_xml.getChild(0)))
            return val

        elif obj_xml.getName() == 'value':
            datatype = None
            for i_attr in range(obj_xml.getAttributesLength()):
                if obj_xml.getAttrPrefix(i_attr) == 'rdf' and obj_xml.getAttrName(i_attr) == 'datatype':
                    datatype = obj_xml.getAttrValue(i_attr)

            if datatype is None:
                raise ValueError('Unable to decode object')

            assert obj_xml.getNumChildren() == 1
            val = libsedml.XMLNode.convertXMLNodeToString(obj_xml.getChild(0))
            if datatype == "http://www.w3.org/2001/XMLSchema#string":
                pass
            elif datatype == "http://www.w3.org/2001/XMLSchema#integer":
                val = int(val)
            elif datatype == "http://www.w3.org/2001/XMLSchema#float":
                val = float(val)
            else:
                raise ValueError("Datatype must be float, integer, or string not {}".format(datatype))
            return val

        else:
            raise ValueError('Unable to decode object')
