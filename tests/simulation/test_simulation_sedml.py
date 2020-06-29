""" Test of SED-ML utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.chart.data_model import Chart, ChartDataField, ChartDataFieldShape, ChartDataFieldType
from Biosimulations_utils.data_model import OntologyTerm, PrimaryResourceMetadata, RemoteFile, ResourceMetadata
from Biosimulations_utils.biomodel import read_biomodel
from Biosimulations_utils.biomodel.data_model import Biomodel, BiomodelVariable, BiomodelFormat
from Biosimulations_utils.simulation import write_simulation, read_simulation, sedml
from Biosimulations_utils.simulation.core import SimulationIoError, SimulationIoWarning
from Biosimulations_utils.simulation.data_model import SimulationFormat, TimecourseSimulation, SimulationResult
from Biosimulations_utils.simulation.sedml import modify_xml_model_for_simulation
from Biosimulations_utils.visualization.data_model import Visualization, VisualizationLayoutElement, VisualizationDataField
import json
import libsedml
import os
import shutil
import tempfile
import unittest


class WriteSedMlTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_gen_sedml(self):
        with open('tests/fixtures/simulation.json', 'rb') as file:
            sim = TimecourseSimulation.from_json(json.load(file))
        self.assertEqual(sim.metadata.name, "simulation 1")
        sim.model = Biomodel(
            id='sbml_model',
            file=RemoteFile(
                id='sbml_model-file',
                name=os.path.join(self.dirname, 'model.sbml.xml'),
                type='application/sbml+xml',
            ),
            format=BiomodelFormat.sbml.value,
            variables=[
                BiomodelVariable(id='species_1', target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']"),
                BiomodelVariable(id='species_2', target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_2']"),
            ],
            metadata=PrimaryResourceMetadata(name='SBML model'),
            _metadata=ResourceMetadata(),
        )
        sim.model.format.version = 'L1V3'
        sim_filename = os.path.join(self.dirname, 'simulation.sedml')
        write_simulation(sim, sim_filename, SimulationFormat.sedml, level=1, version=3)

        sims_2, _ = read_simulation(
            sim_filename, SimulationFormat.sedml)
        self.assertEqual(len(sims_2), 1)
        sim_2 = sims_2[0]
        self.assertEqual(sim_2.id, sim.id)
        self.assertEqual(sim_2.format.version, 'L1V3')
        self.assertEqual(sim_2.format, sim.format)
        self.assertEqual(sim_2.metadata.name, sim.metadata.name)
        self.assertEqual(sim_2.model.id, sim.model.id)
        self.assertEqual(sim_2.model.metadata.name, sim.model.metadata.name)
        self.assertEqual(
            set(v.id for v in sim_2.model.variables),
            set(v.id for v in sim.model.variables))
        self.assertEqual(sim_2.model.file.name, sim.model.file.name)
        self.assertEqual(sim_2.algorithm.id, sim.algorithm.id)
        self.assertEqual(sim_2.algorithm, sim.algorithm)
        self.assertEqual(sim_2._metadata.version, sim._metadata.version)
        self.assertEqual(sim_2._metadata.created, sim._metadata.created)
        self.assertEqual(sim_2._metadata.updated, sim._metadata.updated)
        self.assertEqual(sim_2._metadata, sim._metadata)

        sim_2.metadata.image = sim.metadata.image
        sim_2.metadata.owner = sim.metadata.owner
        sim_2.metadata.access_level = sim.metadata.access_level
        sim_2.metadata.parent = sim.metadata.parent
        self.assertEqual(sim_2.metadata, sim.metadata)
        self.assertEqual(sim_2, sim)

        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_simulation(None, SimulationFormat.sessl)

    def test_gen_sedml_errors(self):
        # Other versions/levels of SED-ML are not supported
        sim = TimecourseSimulation(
            model=Biomodel(
                format=BiomodelFormat.sbml.value,
            ),
            format=SimulationFormat.sedml.value,
        )
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            write_simulation(sim, None, format=SimulationFormat.sedml, level=1, version=1)

        # other simulation experiments formats (e.g., SESSL) are not supported
        sim = TimecourseSimulation(
            model=Biomodel(
                format=BiomodelFormat.sbml.value,
            ),
            format=SimulationFormat.sessl.value,
        )
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            write_simulation(sim, None, SimulationFormat.sessl, level=1, version=3)
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            write_simulation(sim, None, SimulationFormat.sedml, level=1, version=3)

    def test__get_obj_annotation(self):
        reader = sedml.SedMlSimulationReader()

        doc = libsedml.SedDocument()
        self.assertEqual(reader._get_obj_annotation(doc), [])

        doc.setAnnotation('<annotation></annotation>')
        self.assertEqual(reader._get_obj_annotation(doc), [])

        doc.setAnnotation('<annotation><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF></annotation>')
        self.assertEqual(reader._get_obj_annotation(doc), [])

        doc.setAnnotation(
            '<annotation><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description></rdf:Description>'
            '</rdf:RDF></annotation>')
        self.assertEqual(reader._get_obj_annotation(doc), [])

    def test__call_sedml_error(self):
        doc = libsedml.SedDocument()
        with self.assertRaisesRegex(ValueError, 'libsedml error:'):
            sedml.SedMlSimulationWriter._call_libsedml_method(doc, doc, 'setAnnotation', '<rdf')

        with self.assertRaisesRegex(SimulationIoError, 'libsedml error'):
            sedml.SedMlSimulationReader().run('non-existant-file')

    def test_read_with_multiple_models_and_sims_and_unsupported_task(self):
        filename = 'tests/fixtures/Simon2019-with-multiple-models-and-sims.sedml'
        with self.assertWarnsRegex(SimulationIoWarning, 'is not supported'):
            read_simulation(filename, SimulationFormat.sedml)

    def test_read_with_unsupported_simulation(self):
        filename = 'tests/fixtures/Simon2019-with-one-step-sim.sedml'
        with self.assertRaisesRegex(SimulationIoError, 'Unsupported simulation type'):
            read_simulation(filename, SimulationFormat.sedml)

    def test_read_biomodels_sims(self):
        sims, _ = read_simulation('tests/fixtures/Simon2019.sedml', SimulationFormat.sedml)
        self.assertEqual(len(sims), 1)
        sim = sims[0]
        self.assertEqual(sim.model_parameter_changes, [])
        self.assertEqual(sim.start_time, 0.)
        self.assertEqual(sim.output_start_time, 0.)
        self.assertEqual(sim.end_time, 1.)
        self.assertEqual(sim.num_time_points, 100)
        self.assertEqual(sim.algorithm.kisao_term, OntologyTerm(
            ontology='KISAO',
            id='0000019'))
        self.assertEqual(sim.algorithm_parameter_changes, [])

    def test_read_visualizations(self):
        filename = 'tests/fixtures/BIOMD0000000297.sedml'
        sims, viz = read_simulation(filename, SimulationFormat.sedml)
        self.assertEqual(len(viz.layout), 4)

        viz.layout = viz.layout[slice(0, 1)]
        expected = Visualization(
            layout=[
                VisualizationLayoutElement(
                    chart=Chart(id='line'),
                    data=[
                        VisualizationDataField(
                            data_field=ChartDataField(
                                name='x',
                                shape=ChartDataFieldShape.array,
                                type=ChartDataFieldType.dynamic_simulation_result,
                            ),
                            simulation_results=[
                                SimulationResult(simulation=sims[0], variable=BiomodelVariable(id='time', target='urn:sedml:symbol:time')),
                            ],
                        ),
                        VisualizationDataField(
                            data_field=ChartDataField(
                                name='y',
                                shape=ChartDataFieldShape.array,
                                type=ChartDataFieldType.dynamic_simulation_result,
                            ),
                            simulation_results=[
                                SimulationResult(simulation=sims[0], variable=BiomodelVariable(
                                    id='p1_BE_task1',
                                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']")),
                                SimulationResult(simulation=sims[0], variable=BiomodelVariable(
                                    id='p1_BUD_task1',
                                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BUD']")),
                                # SimulationResult(simulation=sims[0], variable=BiomodelVariable(
                                #    id='p1_Clb2_task1',
                                #    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clb2']")),
                                SimulationResult(simulation=sims[0], variable=BiomodelVariable(
                                    id='p1_Cln_task1',
                                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cln']")),
                                SimulationResult(simulation=sims[0], variable=BiomodelVariable(
                                    id='p1_SBF_a_task1',
                                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SBF_a']")),
                                SimulationResult(simulation=sims[0], variable=BiomodelVariable(
                                    id='p1_Sic1_task1',
                                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Sic1']")),
                            ],
                        ),
                    ],
                ),
            ],
        )
        self.assertEqual(viz, expected)

    def test_read_visualizations_with_log_axis(self):
        filename = 'tests/fixtures/BIOMD0000000297-with-log-axis.sedml'
        _, viz = read_simulation(filename, SimulationFormat.sedml)
        self.assertEqual(viz.layout[0].chart.id, 'line_logX_logY')

    def test_read_visualizations_with_consistent_x_axes(self):
        filename = 'tests/fixtures/BIOMD0000000739.sedml'
        read_simulation(filename, SimulationFormat.sedml)

    def test_read_visualizations_with_inconsistent_x_axes(self):
        filename = 'tests/fixtures/BIOMD0000000297-with-invalid-x-axis.sedml'
        with self.assertWarnsRegex(SimulationIoWarning, 'must have the same X axis'):
            read_simulation(filename, SimulationFormat.sedml)

    def test_read_visualizations_with_inconsistent_y_axes(self):
        filename = 'tests/fixtures/BIOMD0000000297-with-invalid-y-axis.sedml'
        with self.assertWarnsRegex(SimulationIoWarning, 'must have the same Y axis'):
            read_simulation(filename, SimulationFormat.sedml)

    def test_read_visualizations_with_duplicate_task_ids(self):
        filename = 'tests/fixtures/BIOMD0000000297-with-duplicate-task-ids.sedml'
        with self.assertWarnsRegex(SimulationIoWarning, 'must have unique ids'):
            read_simulation(filename, SimulationFormat.sedml)

    def test_read_visualizations_with_ref_to_non_existant_task(self):
        filename = 'tests/fixtures/BIOMD0000000297-with-ref-to-non-existant-task.sedml'
        with self.assertWarnsRegex(SimulationIoWarning, 'Unable to interpret curve'):
            read_simulation(filename, SimulationFormat.sedml)

    def test_read_visualizations_with_unknown_model_language(self):
        filename = 'tests/fixtures/BIOMD0000000297-with-unknown-model-language.sedml'
        sims, _ = read_simulation(filename, SimulationFormat.sedml)
        self.assertEqual(sims[0].model.format.sed_urn, 'urn:sedml:language:unknown_language')

    def test_variable_target_is_parameter(self):
        filename = 'tests/fixtures/BIOMD0000000803.sedml'
        _, viz = read_simulation(filename, SimulationFormat.sedml)
        self.assertEqual(viz.layout[0].data[0].simulation_results[0].variable.target,
                         "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='IL7']")
        self.assertEqual(viz.layout[0].data[1].simulation_results[0].variable.target,
                         "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='f_7']")

    def test_modify_model_for_simulation(self):
        in_model_filename = 'tests/fixtures/BIOMD0000000806.xml'
        out_model_filename = os.path.join(self.dirname, 'model.xml')
        simulation_filename = 'tests/fixtures/BIOMD0000000806-with-change-attribute.sedml'
        simulations, _ = read_simulation(simulation_filename)
        simulation = simulations[0]
        self.assertNotEqual(simulation.model_parameter_changes, [])
        modify_xml_model_for_simulation(simulation, in_model_filename, out_model_filename, default_namespace='sbml')

        model2 = read_biomodel(out_model_filename, format=BiomodelFormat.sbml)
        param_target_to_value = {p.target: p.value for p in model2.parameters}
        for change in simulation.model_parameter_changes:
            self.assertEqual(param_target_to_value[change.parameter.target], change.value)

        # invalid simulation configurations
        simulation_filename = 'tests/fixtures/BIOMD0000000806-invalid-change-attribute-target.sedml'
        simulations, _ = read_simulation(simulation_filename)
        with self.assertRaisesRegex(ValueError, 'is not a valid XPATH'):
            modify_xml_model_for_simulation(simulations[0], in_model_filename, out_model_filename, default_namespace='sbml')

        simulation_filename = 'tests/fixtures/BIOMD0000000806-invalid-change-attribute-target-2.sedml'
        simulations, _ = read_simulation(simulation_filename)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            modify_xml_model_for_simulation(simulations[0], in_model_filename, out_model_filename, default_namespace='sbml')
