""" Tests of data model for visualizations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Format, Identifier, JournalReference, License, Person, RemoteFile
from Biosimulations_format_utils.chart_type.data_model import ChartType, ChartTypeDataField, ChartTypeDataFieldShape, ChartTypeDataFieldType
from Biosimulations_format_utils.model.data_model import ModelVariable
from Biosimulations_format_utils.sim.data_model import TimecourseSimulation, SimulationResult
from Biosimulations_format_utils.viz.data_model import Visualization, VisualizationLayoutElement, VisualizationDataField
import unittest


class ChartTypeDataModelTestCase(unittest.TestCase):
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
                                 volume=10, num=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
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
                    chart_type=ChartType(id='line'),
                    data=[
                        VisualizationDataField(
                            data_field=ChartTypeDataField(name='field 1', shape=ChartTypeDataFieldShape.array,
                                                          type=ChartTypeDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=ModelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=ModelVariable(id='var-1')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=ModelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=ModelVariable(id='var-1')),
                            ],
                        ),
                        VisualizationDataField(
                            data_field=ChartTypeDataField(name='field 0', shape=ChartTypeDataFieldShape.array,
                                                          type=ChartTypeDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-4'), variable=ModelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-3'), variable=ModelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=ModelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=ModelVariable(id='var-4')),
                            ],
                        ),
                    ],
                ),
                VisualizationLayoutElement(
                    chart_type=ChartType(id='area'),
                    data=[
                        VisualizationDataField(
                            data_field=ChartTypeDataField(name='field 1', shape=ChartTypeDataFieldShape.array,
                                                          type=ChartTypeDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=ModelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=ModelVariable(id='var-1')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=ModelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=ModelVariable(id='var-1')),
                            ],
                        ),
                        VisualizationDataField(
                            data_field=ChartTypeDataField(name='field 0', shape=ChartTypeDataFieldShape.array,
                                                          type=ChartTypeDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-4'), variable=ModelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-3'), variable=ModelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=ModelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=ModelVariable(id='var-4')),
                            ],
                        ),
                    ],
                )
            ],
        )
        self.assertEqual(Visualization.from_json(viz.to_json()), viz)

    def test_VisualizationLayoutElement(self):
        el = VisualizationLayoutElement(
            chart_type=ChartType(id='line'),
            data=[
                VisualizationDataField(
                    data_field=ChartTypeDataField(name='field 1', shape=ChartTypeDataFieldShape.array, type=ChartTypeDataFieldType.static),
                    simulation_results=[
                        SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=ModelVariable(id='var-2')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=ModelVariable(id='var-1')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=ModelVariable(id='var-2')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=ModelVariable(id='var-1')),
                    ],
                ),
                VisualizationDataField(
                    data_field=ChartTypeDataField(name='field 0', shape=ChartTypeDataFieldShape.array, type=ChartTypeDataFieldType.static),
                    simulation_results=[
                        SimulationResult(simulation=TimecourseSimulation(id='sim-4'), variable=ModelVariable(id='var-4')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-3'), variable=ModelVariable(id='var-4')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=ModelVariable(id='var-4')),
                        SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=ModelVariable(id='var-4')),
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
            data_field=ChartTypeDataField(name='field 1', shape=ChartTypeDataFieldShape.array, type=ChartTypeDataFieldType.static),
            simulation_results=[
                SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=ModelVariable(id='var-2')),
                SimulationResult(simulation=TimecourseSimulation(id='sim-1'), variable=ModelVariable(id='var-1')),
                SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=ModelVariable(id='var-2')),
                SimulationResult(simulation=TimecourseSimulation(id='sim-2'), variable=ModelVariable(id='var-1')),
            ],
        )
        self.assertEqual(VisualizationDataField.from_json(field.to_json()), field)
        self.assertEqual(VisualizationDataField.sort_key(field), (
            ('field 1', 'array', 'static'),
            (('sim-1', 'var-1'), ('sim-1', 'var-2'), ('sim-2', 'var-1'), ('sim-2', 'var-2')),
        ))