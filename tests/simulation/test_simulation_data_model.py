""" Tests of data model for simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Format, JournalReference, License, Person, RemoteFile, Type
from Biosimulations_format_utils.model.data_model import Model, ModelParameter, ModelVariable
from Biosimulations_format_utils.model.sbml import ModelingFramework
from Biosimulations_format_utils.simulation.data_model import (
    Simulation, TimecourseSimulation, SteadyStateSimulation, Algorithm, AlgorithmParameter, ParameterChange,
    SimulationResult)
import unittest


class SimDataModelTestCase(unittest.TestCase):
    def test_TimecourseSimulation(self):
        sim = TimecourseSimulation(
            id='model_1',
            name='model 1',
            image=RemoteFile(name='model.png', type='image/png'),
            description='description',
            tags=['a', 'b', 'c'],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, num=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            format=Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            model=Model(id='model_1', name='model 1'),
            model_parameter_changes=[
                ParameterChange(parameter=ModelParameter(id='param_1', name='param 1', type=Type.float, value=3.5),
                                value=5.3),
            ],
            start_time=0.,
            output_start_time=1.,
            end_time=10.,
            num_time_points=100,
            algorithm=Algorithm(id='00001', name='integrator', kisao_id='KISAO:00001', parameters=[
                AlgorithmParameter(id='param_1', name='param 1', type=Type.float, value=1.2,
                                   recommended_range=[0.12, 12.], kisao_id='KISAO:00001'),
            ]),
            algorithm_parameter_changes=[
                ParameterChange(parameter=AlgorithmParameter(id='param_1', name='param 1', type=Type.float,
                                                             value=1.2, recommended_range=[0.12, 12.],
                                                             kisao_id='KISAO:00001'),
                                value=2.1),
            ]
        )
        self.assertEqual(TimecourseSimulation.from_json(sim.to_json()), sim)
        self.assertEqual(Simulation.from_json(sim.to_json()), sim)

    def test_SteadyStateSimulation(self):
        sim = SteadyStateSimulation(
            id='model_1',
            name='model 1',
            image=RemoteFile(name='model.png', type='image/png'),
            description='description',
            tags=['a', 'b', 'c'],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, num=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            format=Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            model=Model(id='model_1', name='model 1'),
            model_parameter_changes=[
                ParameterChange(parameter=ModelParameter(id='param_1', name='param 1', type=Type.float, value=3.5),
                                value=5.3),
            ],
            algorithm=Algorithm(id='00001', name='integrator', kisao_id='KISAO:00001', parameters=[
                AlgorithmParameter(id='param_1', name='param 1', type=Type.float, value=1.2,
                                   recommended_range=[0.12, 12.], kisao_id='KISAO:00001'),
            ]),
            algorithm_parameter_changes=[
                ParameterChange(parameter=AlgorithmParameter(id='param_1', name='param 1', type=Type.float,
                                                             value=1.2, recommended_range=[0.12, 12.], kisao_id='KISAO:00001'),
                                value=2.1),
            ]
        )
        self.assertEqual(SteadyStateSimulation.from_json(sim.to_json()), sim)
        self.assertEqual(Simulation.from_json(sim.to_json()), sim)

    def test_Algorithm(self):
        alg = Algorithm(
            id='00001',
            name='integrator',
            kisao_id='KISAO:00001',
            synonymous_kisao_ids=['KISAO:00002', 'KISAO:00003'],
            modeling_frameworks=[
                ModelingFramework.logical.value,
                ModelingFramework.flux_balance.value,
            ],
            model_formats=[
                Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            ],
            parameters=[
                AlgorithmParameter(id='param_1', name='param 1', type=Type.float, value=1.2,
                                   recommended_range=[0.12, 12.], kisao_id='KISAO:00001'),
            ],
        )
        self.assertEqual(Algorithm.from_json(alg.to_json()), alg)

    def test_AlgorithmParameter(self):
        param = AlgorithmParameter(id='param_1', name='param 1', type=Type.float, value=1.2,
                                   recommended_range=[0.12, 12.], kisao_id='KISAO:00001')
        self.assertEqual(AlgorithmParameter.from_json(param.to_json()), param)
        self.assertEqual(AlgorithmParameter.sort_key(param), ('param_1', 'param 1', 'float', 1.2, (0.12, 12.), 'KISAO:00001'))

    def test_ParameterChange(self):
        change = ParameterChange(parameter=AlgorithmParameter(id='param_1', name='param 1', type=Type.float, value=1.2,
                                                              recommended_range=[0.12, 12.], kisao_id='KISAO:00001'),
                                 value=2.1)
        self.assertEqual(ParameterChange.from_json(change.to_json(), AlgorithmParameter), change)
        self.assertEqual(ParameterChange.sort_key(change), (('param_1', 'param 1', 'float', 1.2, (0.12, 12.), 'KISAO:00001'), 2.1))

    def test_SimulationResult(self):
        result = SimulationResult(simulation=TimecourseSimulation(id='sim'), variable=ModelVariable(id='var'))
        self.assertEqual(SimulationResult.from_json(result.to_json()), result)
        self.assertEqual(SimulationResult.sort_key(result), ('sim', 'var'))
