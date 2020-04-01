""" Utilities for working with SED-ML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import SimWriter, SimReader
from .data_model import Simulation, Algorithm, AlgorithmParameter, ParameterChange
from ..data_model import Format
from ..model.data_model import Model, Parameter, Variable
from xml.sax import saxutils
import abc
import libsedml

__all__ = [
    'SedMlSimWriter',
    'SedMlSimReader',
]


class SedMlSimWriter(SimWriter):
    """ Base class for SED-ML generator for each model format """

    MODEL_LANGUAGE_URN = None
    MODEL_LANGUAGE_NAME = None

    def run(self, model_vars, sim, model_filename, sim_filename, level=1, version=3):
        """
        Args:
            model_vars (:obj:`list` of :obj:`Variable`): List of variables in the model. Each variable should have the keys `id` and `target`
            sim (:obj:`Simulation`): Simulation experiment
            model_filename (:obj:`str`): Path to the model definition
            sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
            level (:obj:`int`): SED-ML level
            version (:obj:`int`): SED-ML version

        Returns:
            :obj:`libsedml.SedDocument`: SED document
        """
        if sim.format.name != 'SED-ML' or sim.format.version != 'L{}V{}'.format(level, version):
            raise ValueError('Format must be SED-ML L{}V{}'.format(level, version))

        doc_sed = self._create_doc(level, version)
        self._add_metadata_to_doc(sim, doc_sed)

        model_sed = self._add_model_to_doc(sim.model, model_filename, doc_sed)
        self._add_parameter_changes_to_model(sim.model_parameter_changes, doc_sed, model_sed)

        sim_sed = self._add_timecourse_sim_to_doc(sim, doc_sed)
        alg_sed = self._add_algorithm_to_sim(sim.algorithm, doc_sed, sim_sed)
        self._add_param_changes_to_alg(sim.algorithm_parameter_changes, doc_sed, alg_sed)
        task_sed = self._add_sim_task_to_doc(doc_sed, model_sed, sim_sed)

        report_sed = self._add_report_to_doc(doc_sed)
        time_gen_sed = self._add_data_gen_to_doc('time', 'time', doc_sed)
        self._add_var_to_data_gen('time', 'time', 'urn:sedml:symbol:time', doc_sed, time_gen_sed, task_sed)
        self._add_data_set_to_report('time', 'time', doc_sed, report_sed, time_gen_sed)

        self._add_task_results_to_report(model_vars, doc_sed, task_sed, report_sed)

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
        """ Add the metadata about a simulation experiment to the annotation of a SED document

        * Id
        * Name
        * Authors
        * Description
        * Tags
        * References
        * License

        Args:
            sim (:obj:`Simulation`): simulation experiment
            doc_sed (:obj:`libsedml.SedDocument`): SED document
        """
        metadata = {}
        for attr_name in ['id', 'name', 'description', 'tags']:
            attr_val = getattr(sim, attr_name)
            if attr_val:
                metadata[attr_name] = attr_val

        if sim.authors:
            metadata['authors'] = [author.to_json() for author in sim.authors]
        if sim.refs:
            metadata['refs'] = [ref.to_json() for ref in sim.refs]
        if sim.license:
            metadata['license'] = sim.license.value

        self._add_annotation_to_obj(metadata, doc_sed, doc_sed)

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
        self._call_libsedml_method(doc_sed, model_sed, 'setLanguage', self.MODEL_LANGUAGE_URN)
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
        self._call_libsedml_method(doc_sed, change_sed, 'setTarget', change.parameter.target)
        self._add_annotation_to_obj({
            'id': change.parameter.id,
            'name': change.parameter.name,
        }, doc_sed, change_sed)
        self._call_libsedml_method(doc_sed, change_sed, 'setNewValue', str(change.value))
        return change_sed

    def _add_timecourse_sim_to_doc(self, sim, doc_sed):
        """ Add a timecourse simulation to a SED document

        Args:
            sim (:obj:`Simulation`): simulation experiment
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedUniformTimeCourse`: timecourse simulation
        """
        sim_sed = doc_sed.createUniformTimeCourse()
        self._call_libsedml_method(doc_sed, sim_sed, 'setId', 'simulation')
        self._call_libsedml_method(doc_sed, sim_sed, 'setInitialTime', sim.start_time)
        self._call_libsedml_method(doc_sed, sim_sed, 'setOutputStartTime', sim.start_time)
        self._call_libsedml_method(doc_sed, sim_sed, 'setOutputEndTime', sim.end_time)
        self._call_libsedml_method(doc_sed, sim_sed, 'setNumberOfPoints', sim.num_time_points)
        return sim_sed

    def _add_algorithm_to_sim(self, algorithm, doc_sed, sim_sed):
        """ Add a simulation algorithm to a SED document

        Args:
            algorithm (:obj:`Algorithm`): simulation algorithm
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation

        Returns:
            :obj:`libsedml.SedAlgorithm`: SED simulation algorithm
        """
        alg_sed = sim_sed.createAlgorithm()
        self._call_libsedml_method(doc_sed, alg_sed, 'setKisaoID', algorithm.id)
        self._add_annotation_to_obj({'name': algorithm.name}, doc_sed, alg_sed)
        return alg_sed

    def _add_param_changes_to_alg(self, changes, doc_sed, alg_sed):
        """ Add simulation algorithm parameter changes to a SED document

        Args:
            changes (:obj:`list` of :obj:`ParameterChange`): simulation algorithm parameter changes
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
            change (:obj:`ParameterChange`): simulation algorithm parameter change
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            alg_sed (:obj:`libsedml.SedAlgorithm`): SED simulation algorithm

        Returns:
            :obj:`libsedml.SedAlgorithmParameter`: SED simulation algorithm paremeter change
        """
        change_sed = alg_sed.createAlgorithmParameter()
        self._call_libsedml_method(doc_sed, change_sed, 'setKisaoID', change.parameter.kisao_id)
        self._add_annotation_to_obj({'name': change.parameter.name}, doc_sed, change_sed)
        self._call_libsedml_method(doc_sed, change_sed, 'setValue', str(change.value))
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
        self._call_libsedml_method(doc_sed, data_gen_sed, 'setName', name)
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

    def _add_task_results_to_report(self, vars, doc_sed, task_sed, report_sed):
        """ Add simulation predictions to a SED report

        Args:
            vars (:obj:`list` of :obj:`Variable`): variables predicted by a model
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            task_sed (:obj:`libsedml.SedTask`): SED task
            report_sed (:obj:`libsedml.SedReport`): SED report

        Returns:
            :obj:`list` of :obj:`dict`: list of dictionary of data generators and variables for each
                simulation prediction
        """
        seds = []
        for var in vars:
            id = var.id
            data_gen_sed = self._add_data_gen_to_doc(id, id, doc_sed)
            var_sed = self._add_var_to_data_gen(id, id, None, doc_sed, data_gen_sed, task_sed)
            self._call_libsedml_method(doc_sed, var_sed, 'setTarget', var.target)
            self._add_data_set_to_report(id, id, doc_sed, report_sed, data_gen_sed)
            seds.append({
                'data_gen': data_gen_sed,
                'var': var_sed,
            })
        return seds

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
        """ Encode an object into XML

        Args:
            obj (:obj:`object`): object

        Returns:
            :obj:`str`: XML representation of object
        """
        if id:
            id_xml = ' rdf:ID="{}"'.format(id)
        else:
            id_xml = ''

        if isinstance(obj, dict):
            els_xml = []
            for key, val in obj.items():
                els_xml.append(self._encode_obj_to_xml(val, id=key))
            return '<rdf:Description{}>{}</rdf:Description>'.format(id_xml, ''.join(els_xml))
        elif isinstance(obj, set):
            els_xml = []
            for el in obj:
                els_xml.append("<rdf:li>" + self._encode_obj_to_xml(el) + "</rdf:li>")
            return '<rdf:Bag{}>{}</rdf:Bag>'.format(id_xml, ''.join(els_xml))
        elif isinstance(obj, list):
            els_xml = []
            for el in obj:
                els_xml.append("<rdf:li>" + self._encode_obj_to_xml(el) + "</rdf:li>")
            return '<rdf:Seq{}>{}</rdf:Seq>'.format(id_xml, ''.join(els_xml))
        else:
            if isinstance(obj, str):
                datatype = 'string'
                obj_xml = saxutils.escape(obj)
            elif isinstance(obj, int):
                datatype = 'integer'
                obj_xml = obj
            elif isinstance(obj, float):
                datatype = 'float'
                obj_xml = obj
            else:
                raise ValueError('Value must be a float, integer, string, dist, or list not {}'.format(
                    obj.__class__.__name__))
            return ('<rdf:value'
                    '{}'
                    ' rdf:datatype="http://www.w3.org/2001/XMLSchema#{}">'
                    '{}'
                    '</rdf:value>').format(id_xml, datatype, obj_xml)

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


class SedMlSimReader(SimReader):
    def run(self, filename):
        """ Base class for reading a simulation experiment from a SED document

        Args:
            filename (:obj:`str`): path to SED-ML document that describes a simulation experiment

        Returns:
            :obj:`list` of :obj:`Variable`: List of variables in the model. Each variable should have the keys `id` and `target`
            :obj:`Simulation`: Simulation experiment
            :obj:`str`: Path to the model definition
            :obj:`int`: SED-ML level
            :obj:`int`: SED-ML version
        """
        doc_sed = libsedml.readSedMLFromFile(filename)

        assert doc_sed.getNumModels() == 1, "SED-ML document must have one model"
        model_sed = doc_sed.getModel(0)

        assert doc_sed.getNumTasks() == 1, "SED-ML document must have one task"
        task_sed = doc_sed.getTask(0)

        assert doc_sed.getNumSimulations() == 1, "SED-ML document must have one simulation"
        sim_sed = doc_sed.getSimulation(0)

        # model variables
        model_vars = []
        for data_gen_sed in doc_sed.getListOfDataGenerators():
            for var_sed in data_gen_sed.getListOfVariables():
                var_id = var_sed.getId()
                var_id = var_id[len('var_'):]

                if var_id != 'time':
                    model_vars.append(Variable(
                        id=var_id,
                        target=var_sed.getTarget(),
                    ))

        # initialize simulation experiment with metadata
        sim = Simulation.from_json(self._get_obj_annotation(doc_sed))
        sim.format = Format(
            name="SED-ML",
            version="L{}V{}".format(doc_sed.getLevel(), doc_sed.getVersion()),
        )

        # model
        sim.model = Model(
            format=Format(
                name=self.MODEL_LANGUAGE_NAME,
            )
        )

        # model parameter changes
        sim.model_parameter_changes = []
        for change_sed in model_sed.getListOfChanges():
            assert isinstance(change_sed, libsedml.SedChangeAttribute), \
                "Changes must be attribute changes"
            change = self._get_parameter_change_from_model(change_sed)
            sim.model_parameter_changes.append(change)

        # simulation timecourse
        sim.start_time = float(sim_sed.getInitialTime())
        assert float(sim_sed.getOutputStartTime()) == sim.start_time, \
            "Simulation initial time and output start time must be equal"
        sim.end_time = float(sim_sed.getOutputEndTime())
        sim.length = sim.end_time - sim.start_time
        sim.num_time_points = int(sim_sed.getNumberOfPoints())

        # simulation algorithm
        alg_sed = sim_sed.getAlgorithm()
        alg_props = self._get_obj_annotation(alg_sed)
        sim.algorithm = Algorithm(
            id=alg_sed.getKisaoID(),
            name=alg_props.get('name', None),
        )

        # simulation algorithm parameters
        sim.algorithm_parameter_changes = []
        for change_sed in alg_sed.getListOfAlgorithmParameters():
            change_props = self._get_obj_annotation(change_sed)
            sim.algorithm_parameter_changes.append(ParameterChange(
                parameter=AlgorithmParameter(
                    kisao_id=change_sed.getKisaoID(),
                    name=change_props.get('name'),
                ),
                value=float(change_sed.getValue()),
            ))

        # model filename
        model_filename = model_sed.getSource()

        # level and version
        level = doc_sed.getLevel()
        version = doc_sed.getVersion()

        # return simulation experiment
        return (model_vars, sim, model_filename, level, version)

    def _get_parameter_change_from_model(self, change_sed):
        """ Get a model parameter change from a SED change attribute

        Args:
            change_sed (:obj:`libsedml.SedChangeAttribute`): SED change attribute

        Returns:
            obj:`ParameterChange`: model parameter change
        """
        props = self._get_obj_annotation(change_sed)

        return ParameterChange(
            parameter=Parameter(
                id=props.get('id', None),
                name=props.get('name', None),
                target=change_sed.getTarget(),
            ),
            value=float(change_sed.getNewValue())
        )

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
                val = saxutils.unescape(val)
            elif datatype == "http://www.w3.org/2001/XMLSchema#integer":
                val = int(val)
            elif datatype == "http://www.w3.org/2001/XMLSchema#float":
                val = float(val)
            else:
                raise ValueError("Datatype must be float, integer, or string not {}".format(datatype))
            return val

        else:
            raise ValueError('Unable to decode object')
