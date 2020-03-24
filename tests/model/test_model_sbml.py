""" Tests of utilities for working with SBMl-encoded models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.model import ModelFormat, read_model
import importlib
import libsbml
import unittest


class ReadSbmlModelTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        importlib.reload(libsbml)

    def test_run_l2(self):
        filename = 'tests/fixtures/MODEL1204280027.sbml-L2V4.xml'
        model = read_model(filename, format=ModelFormat.sbml)
        self.assertEqual(set(model.keys()), set(['format', 'framework', 'taxon', 'units', 'parameters']))

        self.assertEqual(model['format'], {
            'name': 'SBML',
            'version': 'L2V4',
            'edamId': 'format_2585',
            'url': 'http://sbml.org',
        })

        self.assertEqual(model['framework']['name'], 'non-spatial continuous framework')

        self.assertEqual(model['taxon'], {
            'id': 10090,
            'name': 'Mus musculus',
        })

        self.assertEqual(len(model['parameters']), 37)

        gbl_params = list(filter(lambda param: param['reaction_id'] is None, model['parameters']))
        self.assertEqual(gbl_params, [
            {'reaction_id': None, 'id': 'parameter_1', 'reaction_name': None, 'name': 'quantity_1', 'value': 0.0, 'units': None},
        ])

        lcl_params = list(filter(lambda param: param['reaction_id'] == 'reaction_1', model['parameters']))
        lcl_params.sort(key=lambda param: param['id'])
        self.assertEqual(lcl_params, [
            {'reaction_id': 'reaction_1', 'id': 'k1', 'reaction_name': '15', 'name': 'k1', 'value': 0.02, 'units': None},
            {'reaction_id': 'reaction_1', 'id': 'k2', 'reaction_name': '15', 'name': 'k2', 'value': 1.0, 'units': None},
        ])

        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_model(filename, format=ModelFormat.cellml)

    def test_run_l3(self):
        filename = 'tests/fixtures/BIOMD0000000018.sbml-L3V1.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        self.assertEqual(len(model['parameters']), 107)

        gbl_params = list(filter(lambda param: param['reaction_id'] is None, model['parameters']))
        self.assertEqual(gbl_params, [
            {'reaction_id': None, 'id': 'Keq', 'reaction_name': None, 'name': None, 'value': 0.32, 'units': None},
        ])

        lcl_params = list(filter(lambda param: param['reaction_id'] == 'SHMT', model['parameters']))
        lcl_params.sort(key=lambda param: param['id'])
        self.assertEqual(lcl_params, [
            {'reaction_id': 'SHMT', 'id': 'Km1', 'reaction_name': None, 'name': None, 'value': 1.7, 'units': None},
            {'reaction_id': 'SHMT', 'id': 'Km2', 'reaction_name': None, 'name': None, 'value': 210, 'units': None},
            {'reaction_id': 'SHMT', 'id': 'Vm', 'reaction_name': None, 'name': None, 'value': 18330, 'units': None},
        ])

    def test_run_file_does_not_exist(self):
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            read_model('__non_existant_file__', format=ModelFormat.sbml)

    def test_run_fbc_framework(self):
        filename = 'tests/fixtures/MODEL1904090001.sbml-L3V2.xml'
        model = read_model(filename, format=ModelFormat.sbml)
        self.assertEqual(model['framework']['name'], 'flux balance framework')

    def test_run_units(self):
        filename = 'tests/fixtures/BIOMD0000000821.sbml-L2V4.xml'
        model = read_model(filename, format=ModelFormat.sbml)
        param = list(filter(lambda param: param['id'] == 'lambda_1', model['parameters']))[0]
        self.assertEqual(param['units'], '(8640 second)^-1')
