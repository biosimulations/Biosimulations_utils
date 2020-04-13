""" Tests of utilities for generating and executing COMBINE archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-10
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.archive.exec import gen_archive_for_sim, exec_simulations_in_archive
from Biosimulations_utils.data_model import OntologyTerm
from Biosimulations_utils.biomodel import read_biomodel
from Biosimulations_utils.biomodel.data_model import BiomodelFormat, BiomodelParameter
from Biosimulations_utils.simulation import write_simulation
from Biosimulations_utils.simulation.data_model import (
    TimecourseSimulation, Algorithm, AlgorithmParameter, ParameterChange, SimulationFormat)
import copy
import os
import numpy.testing
import pandas
import shutil
import subprocess
import sys
import tempfile
import unittest


class ExecTestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_name)

    def test(self):
        model_filename = 'tests/fixtures/BIOMD0000000297.xml'
        model = read_biomodel(model_filename, format=BiomodelFormat.sbml)
        model.file.name = 'BIOMD0000000297_url.xml'

        simulation = TimecourseSimulation(
            id='simulation_1',
            name='simulation 1',
            description='Description of simulation 1',
            model=model,
            model_parameter_changes=[
                ParameterChange(parameter=BiomodelParameter(target=param.target), value=0.)
                for param in model.parameters if param.group == 'Initial species amounts/concentrations'
            ],
            start_time=0.,
            output_start_time=0.,
            end_time=10.,
            num_time_points=100,
            algorithm=Algorithm(
                kisao_term=OntologyTerm(
                    ontology='KISAO',
                    id='0000019',
                    name='CVODE',
                ),
            ),
            algorithm_parameter_changes=[
                ParameterChange(
                    parameter=AlgorithmParameter(
                        kisao_term=OntologyTerm(
                            ontology='KISAO',
                            id='0000209',
                        ),
                        name='Relative tolerance',
                    ),
                    value=1e-5,
                ),
                ParameterChange(
                    parameter=AlgorithmParameter(
                        kisao_term=OntologyTerm(
                            ontology='KISAO',
                            id='0000211',
                        ),
                        name='absolute tolerance',
                    ),
                    value=1e-11,
                ),
            ],
            format=copy.copy(SimulationFormat.sedml.value),
        )
        simulation.format.version = 'L1V3'

        archive_filename = os.path.join(self.dir_name, 'archive.omex')
        gen_archive_for_sim(model_filename, simulation, archive_filename)

        out_dir_1 = os.path.join(self.dir_name, 'out')
        exec_simulations_in_archive(archive_filename, self.tellurium_task_executer, out_dir_1)
        self.assert_results_saved(simulation, out_dir_1)

        out_dir_2 = os.path.join(self.dir_name, 'out-tellurium')
        subprocess.check_call(['tellurium', '-i', archive_filename, '-o', out_dir_2])
        self.assert_results_saved(simulation, out_dir_2)

        data_frame_1 = pandas.read_csv(os.path.join(out_dir_1, simulation.id, simulation.id + '.csv'))
        data_frame_2 = pandas.read_csv(os.path.join(out_dir_2, simulation.id, simulation.id + '.csv'))
        numpy.testing.assert_equal(data_frame_1.to_numpy(), data_frame_2.to_numpy())

        # remove parameter changes and re-simulate; check that results are different
        simulation.model_parameter_changes.clear()
        archive_filename_2 = os.path.join(self.dir_name, 'archive2.omex')
        gen_archive_for_sim(model_filename, simulation, archive_filename_2)
        out_dir_3 = os.path.join(self.dir_name, 'out-2')
        exec_simulations_in_archive(archive_filename_2, self.tellurium_task_executer, out_dir_3)
        self.assert_results_saved(simulation, out_dir_3)
        data_frame_3 = pandas.read_csv(os.path.join(out_dir_3, simulation.id, simulation.id + '.csv'))
        with self.assertRaises(AssertionError):
            numpy.testing.assert_equal(data_frame_1.to_numpy(), data_frame_3.to_numpy())

    @staticmethod
    def tellurium_task_executer(model_filename, model_sed_urn, simulation, working_dir, out_filename, out_format):
        ''' Execute a simulation and save its results

        Args:
           model_filename (:obj:`str`): path to the model
           model_sed_urn (:obj:`str`): SED URN for the format of the model (e.g., `urn:sedml:language:sbml`)
           simulation (:obj:`Simulation`): simulation
           working_dir (:obj:`str`): directory of the SED-ML file
           out_filename (:obj:`str`): path to save the results of the simulation
           out_format (:obj:`str`): format to save the results of the simulation (e.g., `csv`)
        '''
        simulation_file_id, simulation_filename = tempfile.mkstemp(suffix='.sedml', dir=working_dir)
        os.close(simulation_file_id)
        write_simulation(simulation, simulation_filename, format=SimulationFormat.sedml)

        tmp_out_dir = tempfile.mkdtemp()
        try:
            subprocess.check_call([
                sys.executable,
                "-c",
                f"""
                import libcombine
                import tellurium.sedml.tesedml
                factory = tellurium.sedml.tesedml.SEDMLCodeFactory(
                    '{simulation_filename}',
                    workingDir='{working_dir}',
                    createOutputs=True,
                    saveOutputs=True,
                    outputDir='{tmp_out_dir}',
                )
                factory.executePython()
                """.replace('\n                ', '\n'),
            ])
            os.rename(os.path.join(tmp_out_dir, simulation.id + '.csv'), out_filename)
        finally:
            os.remove(simulation_filename)
            shutil.rmtree(tmp_out_dir)

    def assert_results_saved(self, simulation, out_dir):
        self.assertEqual(os.listdir(out_dir), [simulation.id])
        self.assertEqual(os.listdir(os.path.join(out_dir, simulation.id)), [simulation.id + '.csv'])
        data_frame = pandas.read_csv(os.path.join(out_dir, simulation.id, simulation.id + '.csv'))
        self.assertEqual(set(data_frame.columns.to_list()), set([var.id for var in simulation.model.variables] + ['time']))
        numpy.testing.assert_array_almost_equal(data_frame['time'], numpy.linspace(0., 10., 101))
