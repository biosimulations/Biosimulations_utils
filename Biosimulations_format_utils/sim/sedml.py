""" Utilities for working with SED-ML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import SimWriter, SimReader, SimIoError, SimIoWarning
from .data_model import (Simulation, TimecourseSimulation, SteadyStateSimulation,  # noqa: F401
                         Algorithm, AlgorithmParameter, ParameterChange)
from ..data_model import Format, JournalReference, License, Person, RemoteFile
from ..model.data_model import Model, ModelParameter, Variable
from ..utils import assert_exception
from datetime import datetime
from xml.sax import saxutils
import enum
import libsedml
import os
import warnings

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
            model_vars (:obj:`list` of :obj:`Variable`): List of variables in the model.
                Each variable should have the keys `id` and `target`
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
        metadata = []
        namespaces = set()

        if sim.id:
            metadata.append(XmlNode(
                prefix='dc',
                name='title',
                children=sim.id,
            ))
            namespaces.add('dc')

        if sim.name:
            metadata.append(XmlNode(
                prefix='dc',
                name='description',
                type='name',
                children=sim.name,
            ))
            namespaces.add('dc')

        if sim.description:
            metadata.append(XmlNode(
                prefix='dc',
                name='description',
                type='description',
                children=sim.description,
            ))
            namespaces.add('dc')

        if sim.tags:
            metadata.append(
                XmlNode(prefix='dc', name='description', type='tags', children=[
                    XmlNode(prefix='rdf', name='Bag', children=[
                        XmlNode(prefix='rdf', name='li', children=[
                            XmlNode(prefix='rdf', name='value', children=tag)
                        ]) for tag in sim.tags
                    ])
                ]))
            namespaces.add('dc')
            namespaces.add('rdf')

        if sim.authors:
            authors_xml = []
            for author in sim.authors:
                names_xml = []
                if author.first_name:
                    names_xml.append(XmlNode(prefix='vcard', name='Given', children=author.first_name))
                if author.middle_name:
                    names_xml.append(XmlNode(prefix='vcard', name='Other', children=author.middle_name))
                if author.last_name:
                    names_xml.append(XmlNode(prefix='vcard', name='Family', children=author.last_name))

                authors_xml.append(XmlNode(prefix='rdf', name='li', children=[
                    XmlNode(prefix='vcard', name='N', children=names_xml)
                ]))

            metadata.append(
                XmlNode(prefix='dc', name='creator', children=[
                    XmlNode(prefix='rdf', name='Bag', children=authors_xml)
                ])
            )
            namespaces.add('dc')
            namespaces.add('rdf')
            namespaces.add('vcard')

        if sim.refs:
            refs_xml = []
            for ref in sim.refs:
                props_xml = []
                if ref.authors:
                    props_xml.append(XmlNode(prefix='bibo', name='authorList', children=ref.authors))
                if ref.title:
                    props_xml.append(XmlNode(prefix='dc', name='title', children=ref.title))
                if ref.journal:
                    props_xml.append(XmlNode(prefix='bibo', name='journal', children=ref.journal))
                if ref.volume:
                    props_xml.append(XmlNode(prefix='bibo', name='volume', children=ref.volume))
                if ref.num:
                    props_xml.append(XmlNode(prefix='bibo', name='issue', children=ref.num))
                if ref.pages:
                    props_xml.append(XmlNode(prefix='bibo', name='pages', children=ref.pages))
                if ref.year:
                    props_xml.append(XmlNode(prefix='dc', name='date', children=ref.year))
                if ref.doi:
                    props_xml.append(XmlNode(prefix='bibo', name='doi', children=ref.doi))

                refs_xml.append(XmlNode(prefix='rdf', name='li', children=[
                    XmlNode(prefix='bibo', name='Article', children=props_xml)
                ]))

            metadata.append(
                XmlNode(prefix='dcterms', name='references', children=[
                    XmlNode(prefix='rdf', name='Bag', children=refs_xml)
                ])
            )
            namespaces.add('dcterms')
            namespaces.add('rdf')
            namespaces.add('bibo')

        if sim.license:
            metadata.append(XmlNode(
                prefix='dcterms',
                name='license',
                children=sim.license.value,
            ))
            namespaces.add('dcterms')

        metadata.append(XmlNode(prefix='dcterms', name='mediator', children='BioSimulations'))
        metadata.append(XmlNode(prefix='dcterms', name='created',
                                children=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
        namespaces.add('dcterms')

        self._add_annotation_to_obj(metadata, doc_sed, doc_sed, namespaces)

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

        metadata = []
        if change.parameter.id:
            metadata.append(XmlNode(
                prefix='dc',
                name='title',
                children=change.parameter.id,
            ))
        if change.parameter.name:
            metadata.append(XmlNode(
                prefix='dc',
                name='description',
                children=change.parameter.name,
            ))
        if metadata:
            self._add_annotation_to_obj(metadata, doc_sed, change_sed, set(['dc']))

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
        self._call_libsedml_method(doc_sed, sim_sed, 'setOutputStartTime', sim.output_start_time)
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
        if algorithm.name:
            self._add_annotation_to_obj([XmlNode(
                prefix='dc',
                name='title',
                children=algorithm.name,
            )], doc_sed, alg_sed, set(['dc']))

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
        if change.parameter.name:
            self._add_annotation_to_obj([XmlNode(
                prefix='dc',
                name='title',
                children=change.parameter.name,
            )], doc_sed, change_sed, set(['dc']))
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
            data_gen_sed (:obj:`libsedml.SedDataGenerator`): SED data generator

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

    def _add_annotation_to_obj(self, nodes, doc_sed, obj_sed, namespaces):
        """ Add annotation to a SED object

        Args:
            nodes (:obj:`list` of :obj:`XmlNode`): annotation
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            obj_sed (:obj:`libsedml.SedBase`): SED object
            namespaces (:obj:`set` of :obj:`str`): list of namespaces
        """
        if nodes:
            namespaces.add('rdf')
            namespaces_xml = []
            if 'rdf' in namespaces:
                namespaces_xml.append(' xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"')
            if 'dc' in namespaces:
                namespaces_xml.append(' xmlns:dc="http://purl.org/dc/elements/1.1/"')
            if 'dcterms' in namespaces:
                namespaces_xml.append(' xmlns:dcterms="http://purl.org/dc/terms/"')
            if 'vcard' in namespaces:
                namespaces_xml.append(' xmlns:vcard="http://www.w3.org/2001/vcard-rdf/3.0#"')
            if 'bibo' in namespaces:
                namespaces_xml.append(' xmlns:bibo="http://purl.org/ontology/bibo/"')

            self._call_libsedml_method(doc_sed, obj_sed, 'setAnnotation',
                                       ('<annotation>'
                                        '  <rdf:RDF{}>'
                                        '    <rdf:Description>'
                                        '    {}'
                                        '    </rdf:Description>'
                                        '  </rdf:RDF>'
                                        '  </annotation>').format(''.join(namespaces_xml), ''.join(node.encode() for node in nodes)))

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
            :obj:`list` of :obj:`Simulation`: simulations
        """
        doc_sed = libsedml.readSedMLFromFile(filename)

        models_sed = {}
        default_model_sed = None
        default_model = None
        for i_model, model_sed in enumerate(doc_sed.getListOfModels()):
            for change_sed in model_sed.getListOfChanges():
                assert_exception(isinstance(change_sed, libsedml.SedChangeAttribute), SimIoError("Changes must be attribute changes"))
            assert_exception(model_sed.getId() not in models_sed, SimIoError("Models must have unique ids"))
            models_sed[model_sed.getId()] = model_sed

            model = Simulation()
            self._read_model(model_sed, model)
            if i_model == 0:
                default_model_sed = model_sed
                default_model = model
            elif model != default_model:
                default_model_sed = None
                default_model = None

        sims_sed = {}
        default_sim_sed = None
        default_sim = None
        for sim_sed in doc_sed.getListOfSimulations():
            assert_exception(sim_sed.getId() not in sims_sed, SimIoError("Simulations must have unique ids"))
            sims_sed[sim_sed.getId()] = sim_sed

            sim = self._create_sim(sim_sed)
            self._read_sim(sim_sed, sim)
            if i_model == 0:
                default_sim_sed = sim_sed
                default_sim = sim
            elif sim != default_sim:
                default_sim_sed = None
                default_sim = None

        # initialize simulation experiment with metadata
        sims = []
        for task_sed in doc_sed.getListOfTasks():
            if not isinstance(task_sed, libsedml.SedTask):
                warnings.warn(
                    '{} {} of {} is not supported'.format(
                        task_sed.__class__.__name__, task_sed.getId(), os.path.basename(filename)),
                    SimIoWarning)
                continue

            sim = self._create_sim(sim_sed)

            # metadata
            self._read_metadata(doc_sed, sim)

            # model
            model_sed = models_sed.get(task_sed.getModelReference(), default_model_sed)
            assert_exception(model_sed is not None, SimIoError("Model cannot be determined"))
            self._read_model(model_sed, sim)
            self._read_model_variables(task_sed, sim)

            # simulation
            sim_sed = sims_sed.get(task_sed.getSimulationReference(), default_sim_sed)
            assert_exception(sim_sed is not None, SimIoError("Simulation cannot be determined"))
            self._read_sim(sim_sed, sim)

            # append simulation to list of simulations
            sims.append(sim)

        # return simulations
        return sims

    def _read_metadata(self, doc_sed, sim):
        """ Read metadata from a SED document

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            sim (:obj:`Simulation`): simulation
        """
        metadata = self._get_obj_annotation(doc_sed)
        for node in metadata:
            if node.prefix == 'dc' and node.name == 'title' and isinstance(node.children, str):
                sim.id = node.children
            elif node.prefix == 'dc' and node.name == 'description' and node.type == 'name' and isinstance(node.children, str):
                sim.name = node.children
            elif node.prefix == 'dc' and node.name == 'description' and node.type == 'description' and isinstance(node.children, str):
                sim.description = node.children
            elif node.prefix == 'dc' and node.name == 'description' and node.type == 'tags':
                for child in node.children:
                    if child.prefix == 'rdf' and child.name == 'Bag':
                        for child_2 in child.children:
                            if child_2.prefix == 'rdf' and child_2.name == 'li':
                                for child_3 in child_2.children:
                                    if child_3.prefix == 'rdf' and child_3.name == 'value' and isinstance(child_3.children, str):
                                        sim.tags.append(child_3.children)
            elif node.prefix == 'dc' and node.name == 'creator':
                for child in node.children:
                    if child.prefix == 'rdf' and child.name == 'Bag':
                        for child_2 in child.children:
                            if child_2.prefix == 'rdf' and child_2.name == 'li':
                                for child_3 in child_2.children:
                                    if child_3.prefix == 'vcard' and child_3.name == 'N':
                                        author = Person()
                                        for prop in child_3.children:
                                            if prop.prefix == 'vcard' and prop.name == 'Given' and isinstance(prop.children, str):
                                                author.first_name = prop.children
                                            elif prop.prefix == 'vcard' and prop.name == 'Other' and isinstance(prop.children, str):
                                                author.middle_name = prop.children
                                            elif prop.prefix == 'vcard' and prop.name == 'Family' and isinstance(prop.children, str):
                                                author.last_name = prop.children
                                        sim.authors.append(author)
            elif node.prefix == 'dcterms' and node.name == 'references':
                for child in node.children:
                    if child.prefix == 'rdf' and child.name == 'Bag':
                        for child_2 in child.children:
                            if child_2.prefix == 'rdf' and child_2.name == 'li':
                                for child_3 in child_2.children:
                                    if child_3.prefix == 'bibo' and child_3.name == 'Article':
                                        ref = JournalReference()
                                        for prop in child_3.children:
                                            if prop.prefix == 'bibo' and prop.name == 'authorList' and isinstance(prop.children, str):
                                                ref.authors = prop.children
                                            elif prop.prefix == 'dc' and prop.name == 'title' and isinstance(prop.children, str):
                                                ref.title = prop.children
                                            elif prop.prefix == 'bibo' and prop.name == 'journal' and isinstance(prop.children, str):
                                                ref.journal = prop.children
                                            elif prop.prefix == 'bibo' and prop.name == 'volume' and isinstance(prop.children, str):
                                                try:
                                                    ref.volume = int(prop.children)
                                                except Exception:
                                                    ref.volume = prop.children
                                            elif prop.prefix == 'bibo' and prop.name == 'issue' and isinstance(prop.children, str):
                                                ref.num = int(prop.children)
                                            elif prop.prefix == 'bibo' and prop.name == 'pages' and isinstance(prop.children, str):
                                                ref.pages = prop.children
                                            elif prop.prefix == 'dc' and prop.name == 'date' and isinstance(prop.children, str):
                                                ref.year = int(prop.children)
                                            elif prop.prefix == 'bibo' and prop.name == 'doi' and isinstance(prop.children, str):
                                                ref.doi = prop.children
                                        sim.refs.append(ref)
            elif node.prefix == 'dcterms' and node.name == 'license' and isinstance(node.children, str):
                sim.license = License(node.children)

        sim.format = Format(
            name="SED-ML",
            version="L{}V{}".format(doc_sed.getLevel(), doc_sed.getVersion()),
        )

    def _read_model(self, model_sed, sim):
        """ Read a SED model

        Args:
            model_sed (:obj:`libsedml.SedModel`): SED model
            sim (:obj:`Simulation`): simulation
        """
        # model
        sim.model = Model(
            format=Format(
                name=self.MODEL_LANGUAGE_NAME,
            ),
            file=RemoteFile(name=model_sed.getSource(), type='application/sbml+xml'),
        )

        # parameter changes
        sim.model_parameter_changes = []
        for change_sed in model_sed.getListOfChanges():
            change = self._get_parameter_change_from_model(change_sed)
            sim.model_parameter_changes.append(change)

    def _read_model_variables(self, task_sed, sim):
        """ Read model variables from SED data generators

        Args:
            task_sed (:obj:`libsedml.Sed`): SED task
            sim (:obj:`Simulation`): simulation
        """
        sim.model.variables = []
        for data_gen_sed in task_sed.getSedDocument().getListOfDataGenerators():
            for var_sed in data_gen_sed.getListOfVariables():
                if var_sed.getTaskReference() == task_sed.getId():
                    var_id = var_sed.getId()
                    var_id = var_id[len('var_'):]

                    if var_id != 'time':
                        sim.model.variables.append(Variable(
                            id=var_id,
                            target=var_sed.getTarget(),
                        ))

    def _create_sim(self, sim_sed):
        """ Create a simulation for a SED simulation

        Args:
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation

        Returns
            :obj:`Simulation`: simulation
        """
        if isinstance(sim_sed, libsedml.SedUniformTimeCourse):
            return TimecourseSimulation()
        elif isinstance(sim_sed, libsedml.SedSteadyState):
            return SteadyStateSimulation()
        else:
            raise SimIoError('Unsupported simulation type: {}'.format(sim_sed.__class__.__name__))

    def _read_sim(self, sim_sed, sim):
        """ Read a SED simulation

        Args:
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation
            sim (:obj:`Simulation`): simulation
        """
        # time course
        if isinstance(sim_sed, libsedml.SedUniformTimeCourse):
            sim.start_time = float(sim_sed.getInitialTime())
            sim.output_start_time = float(sim_sed.getOutputStartTime())
            assert_exception(sim.output_start_time >= sim.start_time,
                             SimIoError("Output time must be at least the start time"))
            sim.end_time = float(sim_sed.getOutputEndTime())
            sim.num_time_points = int(sim_sed.getNumberOfPoints())

        # algorithm
        alg_sed = sim_sed.getAlgorithm()
        alg_props = self._get_obj_annotation(alg_sed)
        alg_name = None
        for node in alg_props:
            if node.prefix == 'dc' and node.name == 'title':
                alg_name = node.children
                break

        sim.algorithm = Algorithm(
            id=alg_sed.getKisaoID(),
            name=alg_name,
        )

        # algorithm parameters
        sim.algorithm_parameter_changes = []
        for change_sed in alg_sed.getListOfAlgorithmParameters():
            change_props = self._get_obj_annotation(change_sed)
            param_name = None
            for node in change_props:
                if node.prefix == 'dc' and node.name == 'title':
                    param_name = node.children
                    break

            sim.algorithm_parameter_changes.append(ParameterChange(
                parameter=AlgorithmParameter(
                    kisao_id=change_sed.getKisaoID(),
                    name=param_name,
                ),
                value=float(change_sed.getValue()),
            ))

    def _get_parameter_change_from_model(self, change_sed):
        """ Get a model parameter change from a SED change attribute

        Args:
            change_sed (:obj:`libsedml.SedChangeAttribute`): SED change attribute

        Returns:
            obj:`ParameterChange`: model parameter change
        """
        props = self._get_obj_annotation(change_sed)
        param_id = None
        param_name = None
        for node in props:
            if node.prefix == 'dc':
                if node.name == 'title':
                    param_id = node.children
                elif node.name == 'description':
                    param_name = node.children

        return ParameterChange(
            parameter=ModelParameter(
                id=param_id,
                name=param_name,
                target=change_sed.getTarget(),
            ),
            value=float(change_sed.getNewValue())
        )

    def _get_obj_annotation(self, obj_sed):
        """ Get the annotated properies of a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object

        Returns:
            :obj:`list` of :obj:`XmlNode`: list of annotations
        """
        annotations_xml = obj_sed.getAnnotation()
        if annotations_xml is None:
            return []

        nodes = []
        if annotations_xml.getPrefix() == '' and annotations_xml.getName() == 'annotation':
            for i_child in range(annotations_xml.getNumChildren()):
                rdf_xml = annotations_xml.getChild(i_child)
                if rdf_xml.getPrefix() == 'rdf' and rdf_xml.getName() == 'RDF':
                    for i_child_2 in range(rdf_xml.getNumChildren()):
                        description_xml = rdf_xml.getChild(i_child_2)
                        if description_xml.getPrefix() == 'rdf' and description_xml.getName() == 'Description':
                            for i_child_3 in range(description_xml.getNumChildren()):
                                child = description_xml.getChild(i_child_3)
                                nodes.append(self._decode_obj_from_xml(child))
        return nodes

    def _decode_obj_from_xml(self, obj_xml):
        """ Decode an object from its XML representation

        Args:
            obj_xml (:obj:`libsedml.XMLNode`): XML representation of an object

        Returns:
            :obj:`XmlNode`: object
        """
        node = XmlNode(
            prefix=obj_xml.getPrefix(),
            name=obj_xml.getName(),
            type=None,
            children=None,
        )

        for i_attr in range(obj_xml.getAttributesLength()):
            if obj_xml.getAttrPrefix(i_attr) == 'dc' and obj_xml.getAttrName(i_attr) == 'type':
                node.type = obj_xml.getAttrValue(i_attr)

        if obj_xml.getNumChildren() == 1 and not obj_xml.getChild(0).getPrefix() and not obj_xml.getChild(0).getName():
            node.children = obj_xml.getChild(0).getCharacters()
        else:
            node.children = []
            for i_child in range(obj_xml.getNumChildren()):
                child_xml = obj_xml.getChild(i_child)
                node.children.append(self._decode_obj_from_xml(child_xml))

        return node


class RdfDataType(str, enum.Enum):
    """ RDF data type """
    string = 'string'
    integer = 'integer'
    float = 'float'
    date_time = 'dateTime'


class XmlNode(object):
    """ XML node, used for annotations

    Attributes:
        prefix (:obj:`str`): tag prefix
        name (:obj:`str`): tag name
        type (:obj:`str`): term type
        children (:obj:`int`, :obj:`float`, :obj:`str`, or :obj:`list` of :obj:`XmlNode`): children
    """

    def __init__(self, prefix=None, name=None, type=None, children=None):
        """
        Args:
            prefix (:obj:`str`, optional): tag prefix
            name (:obj:`str`, optional): tag name
            type (:obj:`str`, optional): term type
            children (:obj:`int`, :obj:`float`, :obj:`str`, or :obj:`list` of :obj:`XmlNode`, optional): children
        """
        self.prefix = prefix
        self.name = name
        self.type = type
        self.children = children

    def encode(self):
        if self.type:
            type = ' dc:type="{}"'.format(self.type)
        else:
            type = ''

        if isinstance(self.children, list):
            value_xml = ''.join(child.encode() for child in self.children)
        elif isinstance(self.children, str):
            value_xml = saxutils.escape(self.children)
        else:
            value_xml = self.children

        return ('<{}:{}'
                '{}>'
                '{}'
                '</{}:{}>').format(self.prefix, self.name,
                                   type, value_xml,
                                   self.prefix, self.name)
