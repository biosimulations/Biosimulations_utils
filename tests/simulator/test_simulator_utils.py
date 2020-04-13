""" Tests of utilities for generating and executing COMBINE archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-10
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.simulation import write_simulation
from Biosimulations_utils.simulation.data_model import SimulationFormat
try:
    from Biosimulations_utils.simulator.testing import SbmlSedmlCombineSimulatorValidator
except ModuleNotFoundError:
    pass
from Biosimulations_utils.simulator.utils import exec_simulations_in_archive
import os
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

    @unittest.skipIf(os.getenv('CI', '0') in ['1', 'true'], 'Docker not setup in CI')
    def test(self):        
        validator = SbmlSedmlCombineSimulatorValidator()
        validator.run('crbm/biosimulations_tellurium')

        model_filename = validator.EXAMPLE_MODEL_FILENAMES[0]
        model = validator._gen_example_model(model_filename)
        simulation = validator._gen_example_simulation(model)
        _, archive_filename = validator._gen_example_archive(model_filename, simulation)
        out_dir_1 = os.path.join(self.dir_name, 'out')
        exec_simulations_in_archive(archive_filename, self.tellurium_task_executer, out_dir_1)
        validator._assert_archive_output_valid(model, simulation, out_dir_1)

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
