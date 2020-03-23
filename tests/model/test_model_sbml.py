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
    def setUpClass(cls):
        importlib.reload(libsbml)

    def test_run(self):
        filename = 'tests/fixtures/MODEL1204280027.sbml-l2v4.xml'
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
