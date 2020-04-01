""" Test of SED-ML utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Format
from Biosimulations_format_utils.model import ModelFormat
from Biosimulations_format_utils.model.data_model import Model, Variable
from Biosimulations_format_utils.sim import SimFormat, write_sim, read_sim, sedml
from Biosimulations_format_utils.sim.data_model import Simulation
import importlib
import json
import libsedml
import os
import shutil
import tempfile
import unittest


class WriteSedMlTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        importlib.reload(libsedml)

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_gen_sedml(self):
        model_vars = [
            Variable(id='species_1', target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']"),
            Variable(id='species_2', target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_2']"),
        ]
        with open('tests/fixtures/simulation.json', 'rb') as file:
            sim = Simulation.from_json(json.load(file))
        model_filename = os.path.join(self.dirname, 'model.sbml.xml')
        sim_filename = os.path.join(self.dirname, 'simulation.sed-ml.xml')
        write_sim(model_vars, sim, model_filename, sim_filename,
                  SimFormat.sedml, level=1, version=3)

        model_vars_2, sim_2, model_filename_2, level, version = read_sim(
            sim_filename, ModelFormat.sbml, SimFormat.sedml)
        self.assertEqual(
            set(s.id for s in model_vars_2),
            set(s.id for s in model_vars))
        self.assertEqual(model_filename_2, model_filename)
        self.assertEqual(sim_2, sim)
        self.assertEqual(level, 1)
        self.assertEqual(version, 3)

        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_sim(None, ModelFormat.sbml, SimFormat.sessl)

        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_sim(None, ModelFormat.cellml, SimFormat.sedml)

    def test_gen_sedml_errors(self):
        # Other versions/levels of SED-ML are not supported
        sim = Simulation(
            model=Model(
                format=Format(
                    name='SBML'
                )
            ),
            format=Format(
                name='SED-ML',
                version='L1V2',
            )
        )
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            write_sim(None, sim, None, None, SimFormat.sedml, level=1, version=3)

        # other simulation experiments formats (e.g., SESSL) are not supported
        sim = Simulation(
            model=Model(
                format=Format(
                    name='SBML'
                )
            ),
            format=Format(
                name='SESSL'
            )
        )
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            write_sim(None, sim, None, None, SimFormat.sessl, level=1, version=3)
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            write_sim(None, sim, None, None, SimFormat.sedml, level=1, version=3)

        # other simulation experiments formats (e.g., SESSL) are not supported
        sim = Simulation(
            model=Model(
                format=Format(
                    name='CellML'
                )
            ),
            format=Format(
                name='SED-ML',
                version='L1V3',
            ),
        )
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            write_sim(None, sim, 'model.sbml.xml', None, SimFormat.sedml, level=1, version=3)

    @unittest.skip('Figure out how to trigger an error that writes to the error log')
    def test__call_sedml_error(self):
        doc = libsedml.SedDocument()
        with self.assertRaisesRegex(ValueError, 'libsedml error:'):
            sedml.SedMlSimWriter._call_libsedml_method(doc, doc, 'setName', 'name')
