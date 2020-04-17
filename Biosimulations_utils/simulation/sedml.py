""" Utilities for working with SED-ML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import SimulationWriter, SimulationReader, SimulationIoError, SimulationIoWarning
from .data_model import (Simulation, TimecourseSimulation, SteadyStateSimulation,  # noqa: F401
                         Algorithm, AlgorithmParameter, ParameterChange, SimulationResult,
                         SimulationFormat)
from ..chart.data_model import Chart, ChartDataField, ChartDataFieldShape, ChartDataFieldType
from ..data_model import Format, JournalReference, License, OntologyTerm, Person, RemoteFile
from ..biomodel.data_model import Biomodel, BiomodelParameter, BiomodelVariable, BiomodelFormat
from ..visualization.data_model import Visualization, VisualizationLayoutElement, VisualizationDataField
from ..utils import assert_exception, get_enum_format_by_attr, logger
from xml.sax import saxutils
import copy
import dateutil.parser
import enum
import libsedml
import logging
import os
import warnings

__all__ = [
    'SedMlSimulationWriter',
    'SedMlSimulationReader',
]


class SedMlSimulationWriter(SimulationWriter):
    """ SED-ML writer

    Attributes:
        _num_meta_id (:obj:`int`): number of assigned meta ids
    """

    def run(self, sim, filename, level=1, version=3, visualization=None):
        """
        Args:
            sim (:obj:`Simulation`): Simulation experiment
            filename (:obj:`str`): Path to save simulation experiment in SED-ML format
            level (:obj:`int`, optional): SED-ML level
            version (:obj:`int`, optional): SED-ML version
            visualization (:obj:`Visualization`, optional): visualization

        Returns:
            :obj:`libsedml.SedDocument`: SED document

        Raises:
            :obj:`ValueError`: the SED-ML version of the simulation and the desired output version are different
        """
        if sim.format.id != 'SED-ML' or sim.format.version != 'L{}V{}'.format(level, version):
            raise ValueError('Format must be SED-ML L{}V{}'.format(level, version))

        self._num_meta_id = 0

        doc_sed = self._create_doc(level, version)
        self._add_metadata_to_obj(sim, doc_sed, doc_sed)

        model_sed = self._add_model_to_doc(sim.model, doc_sed)
        self._add_parameter_changes_to_model(sim.model_parameter_changes, doc_sed, model_sed)

        sim_sed = self._add_sim_to_doc(sim, doc_sed)
        alg_sed = self._add_algorithm_to_sim(sim.algorithm, doc_sed, sim_sed)
        self._add_param_changes_to_alg(sim.algorithm_parameter_changes, doc_sed, alg_sed)
        task_sed = self._add_sim_task_to_doc(sim.id, sim.name, doc_sed, model_sed, sim_sed)

        report_sed = self._add_report_to_doc(sim.id, sim.name, doc_sed)
        time_gen_sed = self._add_data_gen_to_doc('time', 'time', doc_sed)
        self._add_var_to_data_gen('time', 'time', 'urn:sedml:symbol:time', doc_sed, time_gen_sed, task_sed)
        self._add_data_set_to_report('time', 'time', doc_sed, report_sed, time_gen_sed)

        self._add_task_results_to_report(sim.model.variables, doc_sed, task_sed, report_sed)

        if visualization:
            self._add_viz_to_doc(visualization, doc_sed)

        self._export_doc(doc_sed, filename)

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

    def _add_metadata_to_obj(self, obj, doc_sed, obj_sed):
        """ Add the metadata about a resource to the annotation of a SED object

        * Name
        * Authors
        * Description
        * Tags
        * References
        * License

        Args:
            obj (:obj:`object`): object
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            obj_sed (:obj:`libsedml.SedBase`): SED object
        """
        metadata = []
        namespaces = set()

        if obj.description:
            metadata.append(XmlNode(
                prefix='dc',
                name='description',
                type='description',
                children=obj.description,
            ))
            namespaces.add('dc')

        if obj.tags:
            metadata.append(
                XmlNode(prefix='dc', name='description', type='tags', children=[
                    XmlNode(prefix='rdf', name='Bag', children=[
                        XmlNode(prefix='rdf', name='li', children=[
                            XmlNode(prefix='rdf', name='value', children=tag)
                        ]) for tag in obj.tags
                    ])
                ]))
            namespaces.add('dc')
            namespaces.add('rdf')

        if obj.authors:
            authors_xml = []
            for author in obj.authors:
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

        if obj.references:
            refs_xml = []
            for ref in obj.references:
                props_xml = []
                if ref.authors:
                    props_xml.append(XmlNode(prefix='bibo', name='authorList', children=ref.authors))
                if ref.title:
                    props_xml.append(XmlNode(prefix='dc', name='title', children=ref.title))
                if ref.journal:
                    props_xml.append(XmlNode(prefix='bibo', name='journal', children=ref.journal))
                if ref.volume:
                    props_xml.append(XmlNode(prefix='bibo', name='volume', children=ref.volume))
                if ref.issue:
                    props_xml.append(XmlNode(prefix='bibo', name='issue', children=ref.issue))
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

        if obj.license:
            metadata.append(XmlNode(
                prefix='dcterms',
                name='license',
                children=obj.license.value,
            ))
            namespaces.add('dcterms')

        metadata.append(XmlNode(prefix='dcterms', name='mediator', children='BioSimulations'))
        if obj.created:
            metadata.append(XmlNode(prefix='dcterms', name='created',
                                    children=obj.created.strftime('%Y-%m-%dT%H:%M:%SZ')))
        if obj.updated:
            metadata.append(XmlNode(prefix='dcterms', name='date', type='update',
                                    children=obj.updated.strftime('%Y-%m-%dT%H:%M:%SZ')))
        namespaces.add('dcterms')

        self._set_meta_id(doc_sed, obj_sed)
        self._add_annotation_to_obj(metadata, doc_sed, obj_sed, namespaces)

    def _add_model_to_doc(self, model, doc_sed):
        """ Add a model to a SED document

        Args:
            model (:obj:`Biomodel`): model
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedModel`: SED model
        """
        model_sed = doc_sed.createModel()
        if model.id:
            self._call_libsedml_method(doc_sed, model_sed, 'setId', model.id)
        if model.name:
            self._call_libsedml_method(doc_sed, model_sed, 'setName', model.name)
        if model.file and model.file.name:
            self._call_libsedml_method(doc_sed, model_sed, 'setSource', model.file.name)
        if model.format and model.format.sed_urn:
            self._call_libsedml_method(doc_sed, model_sed, 'setLanguage', model.format.sed_urn)
        return model_sed

    def _add_parameter_changes_to_model(self, changes, doc_sed, model_sed):
        """ Add model parameter changes to a SED document

        Args:
            changes (:obj:`list` of :obj:`ParameterChange`): model parameter changes
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
            change (:obj:`ParameterChange`): model parameter change
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
            self._set_meta_id(doc_sed, change_sed)
            self._add_annotation_to_obj(metadata, doc_sed, change_sed, set(['dc']))

        self._call_libsedml_method(doc_sed, change_sed, 'setNewValue', str(change.value))
        return change_sed

    def _add_sim_to_doc(self, sim, doc_sed):
        """ Add a simulation to a SED document

        Args:
            sim (:obj:`Simulation`): simulation experiment
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedUniformTimeCourse`: timecourse simulation
        """
        if isinstance(sim, TimecourseSimulation):
            sim_sed = doc_sed.createUniformTimeCourse()
            self._call_libsedml_method(doc_sed, sim_sed, 'setInitialTime', sim.start_time)
            self._call_libsedml_method(doc_sed, sim_sed, 'setOutputStartTime', sim.output_start_time)
            self._call_libsedml_method(doc_sed, sim_sed, 'setOutputEndTime', sim.end_time)
            self._call_libsedml_method(doc_sed, sim_sed, 'setNumberOfPoints', sim.num_time_points)
        else:
            sim_sed = doc_sed.createSteadyState()

        if sim.id:
            self._call_libsedml_method(doc_sed, sim_sed, 'setId', sim.id)
        if sim.name:
            self._call_libsedml_method(doc_sed, sim_sed, 'setName', sim.name)

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
        if algorithm.kisao_term:
            self._call_libsedml_method(doc_sed, alg_sed, 'setKisaoID', algorithm.kisao_term.ontology + ':' + algorithm.kisao_term.id)

        annotations_xml = []

        if algorithm.id:
            annotations_xml.append(XmlNode(
                prefix='dc',
                name='title',
                children=algorithm.id,
            ))

        if algorithm.name:
            annotations_xml.append(XmlNode(
                prefix='dc',
                name='description',
                children=algorithm.name,
            ))

        if annotations_xml:
            self._set_meta_id(doc_sed, alg_sed)
            self._add_annotation_to_obj(annotations_xml, doc_sed, alg_sed, set(['dc']))

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
        param_sed = alg_sed.createAlgorithmParameter()
        if change.parameter.kisao_term:
            self._call_libsedml_method(doc_sed, param_sed, 'setKisaoID',
                                       change.parameter.kisao_term.ontology + ':' + change.parameter.kisao_term.id)
        annotations_xml = []

        if change.parameter.id:
            annotations_xml.append(XmlNode(
                prefix='dc',
                name='title',
                children=change.parameter.id,
            ))

        if change.parameter.name:
            annotations_xml.append(XmlNode(
                prefix='dc',
                name='description',
                children=change.parameter.name,
            ))

        if annotations_xml:
            # self._set_meta_id(doc_sed, param_sed)
            self._add_annotation_to_obj(annotations_xml, doc_sed, param_sed, set(['dc']))

        self._call_libsedml_method(doc_sed, param_sed, 'setValue', str(change.value))
        return param_sed

    def _add_sim_task_to_doc(self, id, name, doc_sed, model_sed, sim_sed):
        """ Add a task to simulate a model to a SED document

        Args:
            id (:obj:`str`): id
            name (:obj:`str`): name
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation

        Returns:
            :obj:`libsedml.SedTask`: SED task
        """
        task_sed = doc_sed.createTask()
        if id:
            self._call_libsedml_method(doc_sed, task_sed, 'setId', id)
        if name:
            self._call_libsedml_method(doc_sed, task_sed, 'setName', name)
        self._call_libsedml_method(doc_sed, task_sed, 'setModelReference', model_sed.getId())
        self._call_libsedml_method(doc_sed, task_sed, 'setSimulationReference', sim_sed.getId())
        return task_sed

    def _add_report_to_doc(self, id, name, doc_sed):
        """ Add a report to a SED document

        Args:
            id (:obj:`str`): id
            name (:obj:`str`): name
            doc_sed (:obj:`libsedml.SedDocument`): SED document

        Returns:
            :obj:`libsedml.SedReport`: SED report
        """
        report_sed = doc_sed.createReport()
        self._call_libsedml_method(doc_sed, report_sed, 'setId', id)
        if name:
            self._call_libsedml_method(doc_sed, report_sed, 'setName', name)
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
        self._call_libsedml_method(doc_sed, data_gen_sed, 'setId', id)
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
        self._call_libsedml_method(doc_sed, var_sed, 'setId', id)
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
        self._call_libsedml_method(doc_sed, dataset_sed, 'setId', id)
        self._call_libsedml_method(doc_sed, dataset_sed, 'setLabel', name)
        self._call_libsedml_method(doc_sed, dataset_sed, 'setDataReference', data_gen_sed.getId())
        return dataset_sed

    def _add_task_results_to_report(self, vars, doc_sed, task_sed, report_sed):
        """ Add simulation predictions to a SED report

        Args:
            vars (:obj:`list` of :obj:`BiomodelVariable`): variables predicted by a model
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

    def _add_viz_to_doc(self, visualization, doc_sed):
        """ Encode visualization into 2D plots in SED document

        Args:
            visualization (:obj:`Visualization`): visualization
            doc_sed (:obj:`libsedml.SedDocument`): SED document
        """
        for i_layout_el, layout_el in enumerate(visualization.layout):
            x_sim_results = next((field.simulation_results for field in layout_el.data if field.data_field.name == 'x'), None)
            y_sim_results = next((field.simulation_results for field in layout_el.data if field.data_field.name == 'y'), None)
            if not x_sim_results or not y_sim_results:
                continue

            plot_sed = doc_sed.createPlot2D()
            plot_sed.setId("plot_{}".format(i_layout_el + 1))
            plot_sed.setName(" ")

            log_x = '_logX' in layout_el.chart.id
            log_y = '_logY' in layout_el.chart.id

            if len(x_sim_results) == 1:
                x_sim_res = x_sim_results[0]
                for y_sim_res in y_sim_results:
                    self._add_curve_to_plot(x_sim_res, y_sim_res, log_x, log_y, plot_sed)

            elif len(x_sim_results) == len(y_sim_results):
                for x_sim_res, y_sim_res in zip(x_sim_results, y_sim_results):
                    self._add_curve_to_plot(x_sim_res, y_sim_res, log_x, log_y, plot_sed)

    def _add_curve_to_plot(self, x_sim_res, y_sim_res, log_x, log_y, plot_sed):
        """
        Args:
            x_sim_res (:obj:`SimulationResult`): X simulation result
            y_sim_res (:obj:`SimulationResult`): Y simulation result
            log_x (:obj:`bool`): if :obj:`True`, plot X axis in log scale
            log_y (:obj:`bool`): if :obj:`True`, plot Y axis in log scale
            plot_sed (:obj:`libsedml.Plot2D`): plot
        """
        curve_sed = plot_sed.createCurve()
        curve_sed.setId('{}_{}_{}'.format(plot_sed.getId(), y_sim_res.variable.id, x_sim_res.variable.id))

        curve_sed.setLogX(log_x)
        curve_sed.setLogY(log_y)

        if x_sim_res.variable.target == 'urn:sedml:symbol:time':
            curve_sed.setXDataReference("time")
            curve_sed.setName(y_sim_res.variable.name or y_sim_res.variable.id)
        else:
            curve_sed.setXDataReference(x_sim_res.variable.id)
            curve_sed.setName('{} vs. {}'.format(
                y_sim_res.variable.name or y_sim_res.variable.id,
                x_sim_res.variable.name or x_sim_res.variable.id))

        curve_sed.setYDataReference(y_sim_res.variable.id)

    def _export_doc(self, doc_sed, filename):
        """ Export a SED document to an XML file

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            filename (:obj:`str`): path to save document in XML format
        """
        # save the SED document to a file
        libsedml.writeSedML(doc_sed, filename)

    def _set_meta_id(self, doc_sed, obj_sed):
        """ Generate and set a unique meta id for a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object
        """
        self._num_meta_id += 1
        self._call_libsedml_method(doc_sed, obj_sed, 'setMetaId', '_{:08d}'.format(self._num_meta_id))

    def _add_annotation_to_obj(self, nodes, doc_sed, obj_sed, namespaces):
        """ Add annotation to a SED object

        Args:
            nodes (:obj:`list` of :obj:`XmlNode`): annotation
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            obj_sed (:obj:`libsedml.SedBase`): SED object
            namespaces (:obj:`set` of :obj:`str`): list of namespaces
        """
        if nodes:
            meta_id = obj_sed.getMetaId()
            if meta_id:
                about_xml = ' rdf:about="#{}"'.format(meta_id)
            else:
                about_xml = ''

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
                                        '    <rdf:Description{}>'
                                        '    {}'
                                        '    </rdf:Description>'
                                        '  </rdf:RDF>'
                                        '  </annotation>').format(
                                           ''.join(namespaces_xml),
                                           about_xml,
                                           ''.join(node.encode() for node in nodes)))

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

        Raises:
            :obj:`ValueError`: if there was a libSED-ML error
        """
        method = getattr(obj_sed, method_name)
        return_val = method(*args, **kwargs)
        if return_val != 0 or doc_sed.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR):
            raise ValueError('libsedml error: {}'.format(doc_sed.getErrorLog().toString()))
        return return_val


class SedMlSimulationReader(SimulationReader):
    """ SED-ML reader

    Attributes:
        _filename (:obj:`str`): Path to save simulation experiment in SED-ML format
    """

    def run(self, filename):
        """ Base class for reading a simulation experiment from a SED document

        Args:
            filename (:obj:`str`): path to SED-ML document that describes a simulation experiment

        Returns:
            :obj:`tuple`:

                * :obj:`list` of :obj:`Simulation`: simulations
                * :obj:`Visualization`: visualization

        Raises:
            :obj:`SimulationIoError`: if any of the following conditions are met

                * The SED document contains changes other than instances of SedChangeAttribute
                * The models or simulations don't have unique ids
                * A model or simulation references cannot be resolved
        """
        self._filename = filename

        doc_sed = libsedml.readSedMLFromFile(filename)
        if doc_sed.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR):
            raise SimulationIoError('libsedml error: {}'.format(doc_sed.getErrorLog().toString()))

        models_sed = {}
        default_model_sed = None
        default_model = None
        for i_model, model_sed in enumerate(doc_sed.getListOfModels()):
            for change_sed in model_sed.getListOfChanges():
                assert_exception(isinstance(change_sed, libsedml.SedChangeAttribute),
                                 SimulationIoError("Changes in {} must be attribute changes".format(filename)))
            assert_exception(model_sed.getId() not in models_sed, SimulationIoError("Models in {} must have unique ids".format(filename)))
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
            assert_exception(sim_sed.getId() not in sims_sed, SimulationIoError("Simulations in {} must have unique ids".format(filename)))
            sims_sed[sim_sed.getId()] = sim_sed

            sim = self._create_sim(sim_sed)
            self._read_sim(sim_sed, filename, sim)
            if i_model == 0:
                default_sim_sed = sim_sed
                default_sim = sim
            elif sim != default_sim:
                default_sim_sed = None
                default_sim = None

        # initialize simulation experiment with metadata
        sims = []
        task_id_to_sim = {}
        for task_sed in doc_sed.getListOfTasks():
            if not isinstance(task_sed, libsedml.SedTask):
                warnings.warn(
                    '{} {} of {} is not supported'.format(
                        task_sed.__class__.__name__, task_sed.getId(), os.path.basename(filename)),
                    SimulationIoWarning)
                continue

            # simulation
            sim_sed = sims_sed.get(task_sed.getSimulationReference(), default_sim_sed)
            if not sim_sed:
                sim_sed = default_sim_sed
                logger.log(logging.INFO, '{}: simulation reference {} is invalid'.format(self._filename, task_sed.getSimulationReference()))
            assert_exception(sim_sed is not None, SimulationIoError("Simulation {} in {} cannot be determined".format(
                task_sed.getSimulationReference(), filename)))

            sim = self._create_sim(sim_sed)
            sim.id = task_sed.getId() or None
            sim.name = task_sed.getName() or None
            self._read_sim(sim_sed, filename, sim)

            # model
            model_sed = models_sed.get(task_sed.getModelReference(), None)
            if not model_sed:
                model_sed = default_model_sed
                logger.log(logging.INFO, '{}: model reference {} is invalid'.format(self._filename, task_sed.getModelReference()))
            assert_exception(model_sed is not None, SimulationIoError("Model {} in {} cannot be determined".format(
                task_sed.getModelReference(), filename)))
            self._read_model(model_sed, sim)
            self._read_model_variables(task_sed, sim)

            # metadata
            self._read_metadata(doc_sed, sim)

            # append simulation to list of simulations
            sims.append(sim)
            task_id = task_sed.getId()
            if task_id in task_id_to_sim:
                warnings.warn('Tasks of {} must have unique ids'.format(os.path.basename(filename)), SimulationIoWarning)
                logger.log(logging.INFO, '{}: task id {} is not unique'.format(self._filename, task_id))
                task_id_to_sim[task_id] = None
            else:
                task_id_to_sim[task_id] = sim

        # data generators
        data_gen_id_to_task_id = {}
        data_gen_id_to_var_target = {}
        time_data_gen_ids = []
        for data_gen_sed in doc_sed.getListOfDataGenerators():
            if data_gen_sed.getNumParameters() == 0 and data_gen_sed.getNumVariables() == 1 and data_gen_sed.getMath().isCiNumber():
                var_sed = data_gen_sed.getVariable(0)
                data_gen_id = data_gen_sed.getId()
                if data_gen_id in data_gen_id_to_task_id:
                    warnings.warn('Data generators of {} must have unique ids'.format(os.path.basename(filename)), SimulationIoWarning)
                    logger.log(logging.INFO, '{}: data generator id {} is not unique'.format(self._filename, data_gen_id))
                    data_gen_id_to_task_id[data_gen_id] = None
                    data_gen_id_to_var_target[data_gen_id] = None
                else:
                    data_gen_id_to_task_id[data_gen_id] = var_sed.getTaskReference()
                    if var_sed.getTarget():
                        data_gen_id_to_var_target[data_gen_id] = var_sed.getTarget()
                    elif var_sed.getSymbol() == 'urn:sedml:symbol:time':
                        time_data_gen_ids.append(data_gen_id)

        # visualizations (Output > Plot2D)
        viz = Visualization()
        for output_sed in doc_sed.getListOfOutputs():
            if not isinstance(output_sed, libsedml.SedPlot2D):
                warnings.warn('{} of {} is not supported'.format(
                    output_sed.__class__.__name__, os.path.basename(filename)), SimulationIoWarning)
                continue

            x_sim_results = []
            y_sim_results = []
            for curve_sed in output_sed.getListOfCurves():
                x_data_gen_id = curve_sed.getXDataReference()
                y_data_gen_id = curve_sed.getYDataReference()

                x_task_id = data_gen_id_to_task_id.get(x_data_gen_id, None)
                y_task_id = data_gen_id_to_task_id.get(y_data_gen_id, None)
                if not x_task_id:
                    warnings.warn('Unable to interpret curve of {}'.format(os.path.basename(filename)), SimulationIoWarning)
                    logger.log(logging.INFO, '{}: data generator {} cannot be resolved'.format(self._filename, x_data_gen_id))
                    continue
                if not y_task_id:
                    warnings.warn('Unable to interpret curve of {}'.format(os.path.basename(filename)), SimulationIoWarning)
                    logger.log(logging.INFO, '{}: data generator {} cannot be resolved'.format(self._filename, y_data_gen_id))
                    continue

                x_sim = task_id_to_sim.get(x_task_id, None)
                y_sim = task_id_to_sim.get(y_task_id, None)
                if not x_sim:
                    warnings.warn('Unable to interpret curve of {}'.format(os.path.basename(filename)), SimulationIoWarning)
                    logger.log(logging.INFO, '{}: task {} cannot be resolved'.format(self._filename, x_task_id))
                    continue
                if not y_sim:
                    warnings.warn('Unable to interpret curve of {}'.format(os.path.basename(filename)), SimulationIoWarning)
                    logger.log(logging.INFO, '{}: task {} cannot be resolved'.format(self._filename, y_task_id))
                    continue

                x_var = self._get_model_var_by_data_gen_id(x_data_gen_id, data_gen_id_to_var_target,
                                                           time_data_gen_ids, x_sim.model.variables)
                y_var = self._get_model_var_by_data_gen_id(y_data_gen_id, data_gen_id_to_var_target,
                                                           time_data_gen_ids, y_sim.model.variables)

                x_sim_results.append(SimulationResult(simulation=x_sim, variable=x_var))
                y_sim_results.append(SimulationResult(simulation=y_sim, variable=y_var))

            if len(set([(curve_sed.getXDataReference(), curve_sed.getLogX()) for curve_sed in output_sed.getListOfCurves()])) == 1:
                x_sim_results = x_sim_results[slice(0, 1)]
            elif not all([sim_res.variable.target == 'urn:sedml:symbol:time' for sim_res in x_sim_results]) or \
                    len(set([curve_sed.getLogX() for curve_sed in output_sed.getListOfCurves()])) > 1:
                warnings.warn('Curves of {} in {} must have the same X axis'.format(output_sed.getId(), filename), SimulationIoWarning)
                logger.log(logging.INFO, '{}: curves of {} have incompatible X axes'.format(self._filename, output_sed.getId()))
                continue

            if len(set([curve_sed.getLogY() for curve_sed in output_sed.getListOfCurves()])) > 1:
                warnings.warn('Curves if {} in {} must have the same Y axis'.format(output_sed.getId(), filename), SimulationIoWarning)
                logger.log(logging.INFO, '{}: curves of {} have incompatible Y axes'.format(self._filename, output_sed.getId()))
                continue

            if not x_sim_results or not y_sim_results:
                continue

            chart_id = 'line'
            if output_sed.getCurve(0).getLogX():
                chart_id += '_logX'
            if output_sed.getCurve(0).getLogY():
                chart_id += '_logY'

            layout_el = VisualizationLayoutElement(
                chart=Chart(id=chart_id),
                data=[
                    VisualizationDataField(
                        data_field=ChartDataField(
                            name='x',
                            shape=ChartDataFieldShape.array,
                            type=ChartDataFieldType.dynamic_simulation_result,
                        ),
                        simulation_results=x_sim_results,
                    ),
                    VisualizationDataField(
                        data_field=ChartDataField(
                            name='y',
                            shape=ChartDataFieldShape.array,
                            type=ChartDataFieldType.dynamic_simulation_result,
                        ),
                        simulation_results=y_sim_results,
                    ),
                ],
            )
            viz.layout.append(layout_el)

        if not viz.layout:
            viz = None

        # return simulations and visualizations
        return (sims, viz)

    def _read_metadata(self, doc_sed, sim):
        """ Read metadata from a SED document

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            sim (:obj:`Simulation`): simulation
        """
        metadata = self._get_obj_annotation(doc_sed)
        for node in metadata:
            if node.prefix == 'dc' and node.name == 'description' and node.type == 'description' and isinstance(node.children, str):
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
                                                ref.issue = int(prop.children)
                                            elif prop.prefix == 'bibo' and prop.name == 'pages' and isinstance(prop.children, str):
                                                ref.pages = prop.children
                                            elif prop.prefix == 'dc' and prop.name == 'date' and isinstance(prop.children, str):
                                                ref.year = int(prop.children)
                                            elif prop.prefix == 'bibo' and prop.name == 'doi' and isinstance(prop.children, str):
                                                ref.doi = prop.children
                                        sim.references.append(ref)
            elif node.prefix == 'dcterms' and node.name == 'license' and isinstance(node.children, str):
                sim.license = License(node.children)
            elif node.prefix == 'dcterms' and node.name == 'created' and isinstance(node.children, str):
                sim.created = dateutil.parser.parse(node.children)
            elif node.prefix == 'dcterms' and node.name == 'date' and node.type == 'update' and isinstance(node.children, str):
                sim.updated = dateutil.parser.parse(node.children)

        sim.format = copy.copy(SimulationFormat.sedml.value)
        sim.format.version = "L{}V{}".format(doc_sed.getLevel(), doc_sed.getVersion())

    def _read_model(self, model_sed, sim):
        """ Read a SED model

        Args:
            model_sed (:obj:`libsedml.SedModel`): SED model
            sim (:obj:`Simulation`): simulation
        """
        # model
        sed_urn = model_sed.getLanguage()
        format = get_enum_format_by_attr(BiomodelFormat, 'sed_urn', sed_urn)
        if not format:
            format = Format(sed_urn=sed_urn)
        sim.model = Biomodel(
            id=model_sed.getId() or None,
            name=model_sed.getName() or None,
            format=format,
            file=RemoteFile(name=model_sed.getSource(), type=format.mime_type),
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
            if data_gen_sed.getNumParameters() == 0 and data_gen_sed.getNumVariables() == 1 and data_gen_sed.getMath().isCiNumber():
                for var_sed in data_gen_sed.getListOfVariables():
                    if var_sed.getTarget() and var_sed.getTaskReference() == task_sed.getId():
                        var_id = var_sed.getId()
                        if var_id != 'time':
                            sim.model.variables.append(BiomodelVariable(
                                id=var_id,
                                target=var_sed.getTarget(),
                            ))

    def _create_sim(self, sim_sed):
        """ Create a simulation for a SED simulation

        Args:
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation

        Returns
            :obj:`Simulation`: simulation

        Raises:
            :obj:`SimulationIoError`: if the simulation type is not supported
        """
        if isinstance(sim_sed, libsedml.SedUniformTimeCourse):
            return TimecourseSimulation()
        elif isinstance(sim_sed, libsedml.SedSteadyState):
            return SteadyStateSimulation()
        else:
            raise SimulationIoError('Unsupported simulation type: {}'.format(sim_sed.__class__.__name__))

    def _read_sim(self, sim_sed, sim_filename, sim):
        """ Read a SED simulation

        Args:
            sim_sed (:obj:`libsedml.SedSimulation`): SED simulation
            sim_filename (:ob:`str`): path to SED-ML file in which SED simulation was defined
            sim (:obj:`Simulation`): simulation

        Raises:
            :obj:`SimulationIoError`: the output start time is less than the start time
            :obj:`AssertionError`: a KiSAO term uses a different ontology or doesn't have an id
        """
        # time course
        if isinstance(sim_sed, libsedml.SedUniformTimeCourse):
            sim.start_time = float(sim_sed.getInitialTime())
            sim.output_start_time = float(sim_sed.getOutputStartTime())
            assert_exception(sim.output_start_time >= sim.start_time,
                             SimulationIoError("Output start time must in {} be at least the start time".format(sim_filename)))
            sim.end_time = float(sim_sed.getOutputEndTime())
            sim.num_time_points = int(sim_sed.getNumberOfPoints())

        # algorithm
        alg_sed = sim_sed.getAlgorithm()
        alg_props = self._get_obj_annotation(alg_sed)
        alg_id = None
        alg_name = None
        for node in alg_props:
            if node.prefix == 'dc' and node.name == 'title':
                alg_id = node.children
            elif node.prefix == 'dc' and node.name == 'description':
                alg_name = node.children

        kisao_term_onto_id = alg_sed.getKisaoID()
        if kisao_term_onto_id:
            kisao_term_onto, _, kisao_term_id = kisao_term_onto_id.partition(':')
            assert kisao_term_onto == 'KISAO'
            assert kisao_term_id
            kisao_term = OntologyTerm(
                ontology=kisao_term_onto,
                id=kisao_term_id,
            )
        else:
            kisao_term = None  # pragma: no cover # unreachable because SED requires kisaoID to be set

        sim.algorithm = Algorithm(
            id=alg_id,
            name=alg_name,
            kisao_term=kisao_term,
        )

        # algorithm parameters
        sim.algorithm_parameter_changes = []
        for change_sed in alg_sed.getListOfAlgorithmParameters():
            change_props = self._get_obj_annotation(change_sed)
            param_id = None
            param_name = None
            for node in change_props:
                if node.prefix == 'dc' and node.name == 'title':
                    param_id = node.children
                elif node.prefix == 'dc' and node.name == 'description':
                    param_name = node.children

            kisao_term_onto_id = change_sed.getKisaoID()
            if kisao_term_onto_id:
                kisao_term_onto, _, kisao_term_id = kisao_term_onto_id.partition(':')
                assert kisao_term_onto == 'KISAO'
                assert kisao_term_id
                kisao_term = OntologyTerm(
                    ontology=kisao_term_onto,
                    id=kisao_term_id,
                )
            else:
                kisao_term = None  # pragma: no cover # unreachable because SED requires kisaoID to be set
            sim.algorithm_parameter_changes.append(ParameterChange(
                parameter=AlgorithmParameter(
                    id=param_id,
                    name=param_name,
                    kisao_term=kisao_term,
                ),
                value=float(change_sed.getValue()),
            ))

    def _get_parameter_change_from_model(self, change_sed):
        """ Get a model parameter change from a SED change attribute

        Args:
            change_sed (:obj:`libsedml.SedChangeAttribute`): SED change attribute

        Returns:
            :obj:`ParameterChange`: model parameter change
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
            parameter=BiomodelParameter(
                id=param_id,
                name=param_name,
                target=change_sed.getTarget(),
            ),
            value=float(change_sed.getNewValue())
        )

    def _get_model_var_by_data_gen_id(self, data_gen_id, data_gen_id_to_var_target, time_data_gen_ids, variables):
        """ Get a model variable by the data generator which records it

        Args:
            data_gen_id (:obj:`str`): id of data generator
            data_gen_id_to_var_target (:obj:`dict`): dictionary that maps the ids of data generators to the targets of model variables
            time_data_gen_ids (:obj:`list` of :obj:`str`): list of ids of data generators that represent time
            variables (:obj:`list` of :obj:`BiomodelVariable`): model variables

        Returns:
            :obj:`BiomodelVariable`: variable
        """
        if data_gen_id in time_data_gen_ids:
            return BiomodelVariable(id='time', target='urn:sedml:symbol:time')
        else:
            return next(var for var in variables if var.target == data_gen_id_to_var_target[data_gen_id])

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
                            description_about_obj = not obj_sed.getMetaId()
                            for i_attr in range(description_xml.getAttributesLength()):
                                if description_xml.getAttrPrefix(i_attr) == 'rdf' \
                                        and description_xml.getAttrName(i_attr) == 'about' \
                                        and description_xml.getAttrValue(i_attr) == '#' + obj_sed.getMetaId():
                                    description_about_obj = True
                                    break
                            if not description_about_obj:
                                continue
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
