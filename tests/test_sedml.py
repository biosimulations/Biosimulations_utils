""" Test of SED-ML utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils import sedml
import json
import libsedml
import os
import shutil
import tempfile
import unittest


class GenSedMlTestCase(unittest.TestCase):
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
        sedml.gen_sedml(model_species, sim, model_filename, sim_filename)

        doc = libsedml.readSedMLFromFile(sim_filename)

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
            sedml.gen_sedml(None, sim, None, None)

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
            sedml.gen_sedml(None, sim, None, None)

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
            sedml.gen_sedml(None, sim, 'model.sbml.xml', None)

    def test__format_person_name(self):
        self.assertEqual(sedml.SedMlGenerator._format_person_name({'firstName': 'John'}), 'John')
        self.assertEqual(sedml.SedMlGenerator._format_person_name({'lastName': 'Doe'}), 'Doe')
        self.assertEqual(sedml.SedMlGenerator._format_person_name({'firstName': 'John', 'lastName': 'Doe'}), 'John Doe')
        self.assertEqual(sedml.SedMlGenerator._format_person_name(
            {'firstName': 'John', 'middleName': 'C', 'lastName': 'Doe'}), 'John C Doe')

    def test__call_sedml_error(self):
        doc = libsedml.SedDocument()
        with self.assertRaisesRegex(ValueError, 'libsedml error:'):
            sedml.SedMlGenerator._call_libsedml_method(doc, doc, 'setName', 'name')
