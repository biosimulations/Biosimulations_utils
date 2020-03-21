""" Test of SED-ML utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils import sedml
from Biosimulations_format_utils.sedml import sbml
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
        model_species = [
            {'id': 'species_1'},
            {'id': 'species_2'},
        ]
        with open('tests/fixtures/simulation.json', 'rb') as file:
            sim = json.load(file)
        model_filename = os.path.join(self.dirname, 'model.sbml.xml')
        sim_filename = os.path.join(self.dirname, 'simulation.sed-ml.xml')
        doc_sed = sedml.write_sedml(model_species, sim, model_filename, sim_filename)

        model_species_2, sim_2, model_filename_2, level, version = sedml.read_sedml(sim_filename)
        self.assertEqual(
            set(s['id'] for s in model_species_2),
            set(s['id'] for s in model_species))
        self.assertEqual(model_filename_2, model_filename)
        self.assertEqual(sim_2, sim)
        self.assertEqual(level, 1)
        self.assertEqual(version, 3)

    def test_gen_sedml_errors(self):
        # Other versions/levels of SED-ML are not supported
        sim = {
            'model': {
                'format': {
                    'name': 'SBML'
                }
            },
            'format': {
                'name': 'SED-ML',
                'version': 'L1V2',
            }
        }
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            sedml.write_sedml(None, sim, None, None)

        # other simulation experiments formats (e.g., SESSL) are not supported
        sim = {
            'model': {
                'format': {
                    'name': 'SBML'
                }
            },
            'format': {
                'name': 'SESSL'
            }
        }
        with self.assertRaisesRegex(ValueError, 'Format must be SED-ML'):
            sedml.write_sedml(None, sim, None, None)

        # other simulation experiments formats (e.g., SESSL) are not supported
        sim = {
            'model': {
                'format': {
                    'name': 'CellML'
                }
            },
            'format': {
                'name': 'SED-ML',
                'version': 'L1V3',
            },
        }
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            sedml.write_sedml(None, sim, 'model.sbml.xml', None)

    def test__call_sedml_error(self):
        doc = libsedml.SedDocument()
        with self.assertRaisesRegex(ValueError, 'libsedml error:'):
            sedml.SedMlWriter._call_libsedml_method(doc, doc, 'setName', 'name')
