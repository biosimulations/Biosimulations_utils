""" Tests of data model for visualizations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.data_model import Format, Identifier, JournalReference, License, Person, RemoteFile
from Biosimulations_utils.chart.data_model import Chart, ChartDataField, ChartDataFieldShape, ChartDataFieldType
from Biosimulations_utils.biomodel.data_model import BiomodelVariable
from Biosimulations_utils.simulation.data_model import TimecourseSimulation, SimulationResult
from Biosimulations_utils.visualization.data_model import Visualization, VisualizationLayoutElement, VisualizationDataField
import unittest


class ChartDataModelTestCase(unittest.TestCase):
    def test_Visualization(self):
        viz = Visualization(
            id='viz_1',
            name='viz 1',
            image=RemoteFile(name='viz.png', type='image/png'),
            description='description',
            tags=['a', 'b', 'c'],
            identifiers=[Identifier(namespace='biomodels.db', id='XXX')],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            format=Format(name='Vega', version='5.10.1', url='https://vega.github.io/vega/'),
            columns=3,
            layout=[
                VisualizationLayoutElement(
                    chart=Chart(id='line'),
                    data=[
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 1',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-1')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-1')),
                            ],
                        ),
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 0',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-4'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-3'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-4')),
                            ],
                        ),
                    ],
                ),
                VisualizationLayoutElement(
                    chart=Chart(id='area'),
                    data=[
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 1',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-1')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-1')),
                            ],
                        ),
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 0',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-4'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-3'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-4')),
                            ],
                        ),
                    ],
                )
            ],
        )
        self.assertEqual(Visualization.from_json(viz.to_json()), viz)

    def test_VisualizationLayoutElement(self):
        el = VisualizationLayoutElement(
            chart=Chart(id='line'),
            data=[
                VisualizationDataField(
                    data_field=ChartDataField(name='field 1', shape=ChartDataFieldShape.array, type=ChartDataFieldType.static),
                    simulation_results=[
                        SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=BiomodelVariable(id='var-2')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=BiomodelVariable(id='var-1')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=BiomodelVariable(id='var-2')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=BiomodelVariable(id='var-1')),
                    ],
                ),
                VisualizationDataField(
                    data_field=ChartDataField(name='field 0', shape=ChartDataFieldShape.array, type=ChartDataFieldType.static),
                    simulation_results=[
                        SimulationResult(simulation=TimecourseSimulation(id='sim-4'), variable=BiomodelVariable(id='var-4')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-3'), variable=BiomodelVariable(id='var-4')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=BiomodelVariable(id='var-4')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=BiomodelVariable(id='var-4')),
                    ],
                ),
            ],
        )
        self.assertEqual(VisualizationLayoutElement.from_json(el.to_json()), el)
        self.assertEqual(VisualizationLayoutElement.sort_key(el), (
            'line',
            (
                (
                    ('field 0', 'array', 'static'),
                    (('sim-1', 'var-4'), ('sim-2', 'var-4'), ('sim-3', 'var-4'), ('sim-4', 'var-4')),
                ),
                (
                    ('field 1', 'array', 'static'),
                    (('sim-1', 'var-1'), ('sim-1', 'var-2'), ('sim-2', 'var-1'), ('sim-2', 'var-2')),
                )
            )
        ))

    def test_VisualizationDataField(self):
        field = VisualizationDataField(
            data_field=ChartDataField(name='field 1', shape=ChartDataFieldShape.array, type=ChartDataFieldType.static),
            simulation_results=[
                SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=BiomodelVariable(id='var-2')),
                SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=BiomodelVariable(id='var-1')),
                SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=BiomodelVariable(id='var-2')),
                SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=BiomodelVariable(id='var-1')),
            ],
        )
        self.assertEqual(VisualizationDataField.from_json(field.to_json()), field)
        self.assertEqual(VisualizationDataField.sort_key(field), (
            ('field 1', 'array', 'static'),
            (('sim-1', 'var-1'), ('sim-1', 'var-2'), ('sim-2', 'var-1'), ('sim-2', 'var-2')),
        ))
