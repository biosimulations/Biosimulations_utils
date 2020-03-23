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
        self.assertEqual(set(model.keys()), set(['parameters']))

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
        self.assertEqual(set(model.keys()), set(['parameters']))

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
