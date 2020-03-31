""" Tests of utilities for working with SBMl-encoded models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.model import ModelFormat, read_model
from Biosimulations_format_utils.model.core import ModelIoError
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
        self.assertEqual(set(model.keys()), set(['format', 'framework', 'taxon', 'units', 'parameters', 'variables']))

        # metadata
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

        # parameters
        self.assertEqual(len(model['parameters']), 37)

        gbl_params = list(filter(lambda param: '.' not in param['id'], model['parameters']))
        self.assertEqual(gbl_params, [
            {
                'target': "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='parameter_1']/@value",
                'id': 'parameter_1',
                'name': 'quantity_1',
                'value': 0.0,
                'units': None
            },
        ])

        lcl_params = list(filter(lambda param: param['id'].startswith('reaction_1.'), model['parameters']))
        lcl_params.sort(key=lambda param: param['id'])
        self.assertEqual(lcl_params, [
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='reaction_1']"
                           "/sbml:kineticLaw/sbml:listOfParameters/sbml:parameter[@id='k1']/@value"),
                'id': 'reaction_1.k1',
                'name': '15: k1',
                'value': 0.02,
                'units': None
            },
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='reaction_1']"
                           "/sbml:kineticLaw/sbml:listOfParameters/sbml:parameter[@id='k2']/@value"),
                'id': 'reaction_1.k2',
                'name': '15: k2',
                'value': 1.0,
                'units': None
            },
        ])

        # variables
        self.assertEqual(len(model['variables']), 24)
        var = next(var for var in model['variables'] if var['id'] == 'species_1')
        self.assertEqual(var, {
            'target': "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']",
            'id': 'species_1',
            'name': 'MK',
            'compartment_id': 'compartment_1',
            'compartment_name': 'compartment',
            'units': '10^-6 mole / liter',
            'constant': False,
            'boundary_condition': False,
        })

        # errors
        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_model(filename, format=ModelFormat.cellml)

    def test_run_l3(self):
        filename = 'tests/fixtures/BIOMD0000000018.sbml-L3V1.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        self.assertEqual(len(model['parameters']), 107)

        gbl_params = list(filter(lambda param: '.' not in param['id'], model['parameters']))
        self.assertEqual(gbl_params, [
            {
                'target': "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='Keq']/@value",
                'id': 'Keq',
                'name': None,
                'value': 0.32,
                'units': None
            },
        ])

        lcl_params = list(filter(lambda param: param['id'].startswith('SHMT.'), model['parameters']))
        lcl_params.sort(key=lambda param: param['id'])
        self.assertEqual(lcl_params, [
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                           "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Km1']/@value"),
                'id': 'SHMT.Km1',
                'name': None,
                'value': 1.7,
                'units': None
            },
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                           "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Km2']/@value"),
                'id': 'SHMT.Km2',
                'name': None,
                'value': 210,
                'units': None
            },
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                           "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Vm']/@value"),
                'id': 'SHMT.Vm',
                'name': None,
                'value': 18330,
                'units': None
            },
        ])

    def test_run_file_does_not_exist(self):
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            read_model('__non_existant_file__', format=ModelFormat.sbml)

    def test_run_fbc_framework(self):
        filename = 'tests/fixtures/MODEL1904090001.sbml-L3V2.xml'
        with self.assertRaisesRegex(ModelIoError, 'packages are not supported'):
            model = read_model(filename, format=ModelFormat.sbml)

    def test_run_units(self):
        filename = 'tests/fixtures/BIOMD0000000821.sbml-L2V4.xml'
        model = read_model(filename, format=ModelFormat.sbml)
        param = list(filter(lambda param: param['id'] == 'lambda_1', model['parameters']))[0]
        self.assertEqual(param['units'], '1.157 10^-4 1 / second')
