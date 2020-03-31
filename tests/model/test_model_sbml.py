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
        other_params = list(filter(lambda param: param['group'] == 'Other parameters', model['parameters']))
        self.assertEqual(len(other_params), 37)

        gbl_params = list(filter(lambda param: '.' not in param['id'], other_params))
        self.assertEqual(gbl_params, [
            {
                'target': "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='parameter_1']/@value",
                'group': 'Other parameters',
                'id': 'parameter_1',
                'name': 'quantity_1',
                'value': 0.0,
                'units': None
            },
        ])

        lcl_params = list(filter(lambda param: param['id'].startswith('reaction_1.'), other_params))
        lcl_params.sort(key=lambda param: param['id'])
        self.assertEqual(lcl_params, [
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='reaction_1']"
                           "/sbml:kineticLaw/sbml:listOfParameters/sbml:parameter[@id='k1']/@value"),
                'group': 'Other parameters',
                'id': 'reaction_1.k1',
                'name': '15: k1',
                'value': 0.02,
                'units': None
            },
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='reaction_1']"
                           "/sbml:kineticLaw/sbml:listOfParameters/sbml:parameter[@id='k2']/@value"),
                'group': 'Other parameters',
                'id': 'reaction_1.k2',
                'name': '15: k2',
                'value': 1.0,
                'units': None
            },
        ])

        init_comp_size_params = list(filter(lambda param: param['group'] == 'Initial compartment sizes', model['parameters']))
        self.assertEqual(init_comp_size_params, [{
            'target': "/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='compartment_1']/@size",
            'group': 'Initial compartment sizes',
            'id': 'init_size_compartment_1',
            'name': 'Initial size of compartment',
            'value': 1.0,
            'units': '10^-3 liter',
        }])

        init_species_params = list(filter(lambda param: param['group'] == 'Initial species amounts/concentrations', model['parameters']))
        init_species_param = next(param for param in init_species_params if param['id'] == 'init_concentration_species_1')
        self.assertEqual(init_species_param, {
            'target': "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']/@initialConcentration",
            'group': 'Initial species amounts/concentrations',
            'id': 'init_concentration_species_1',
            'name': 'Initial concentration of MK',
            'value': 1200.,
            'units': None,
        })

        # variables
        self.assertEqual(len(model['variables']), 24)
        var = next(var for var in model['variables'] if var['id'] == 'species_1')
        self.assertEqual(var, {
            'target': "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']",
            'group': 'Species amounts/concentrations',
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

        other_params = list(filter(lambda param: param['group'] == 'Other parameters', model['parameters']))
        self.assertEqual(len(other_params), 107)

        gbl_params = list(filter(lambda param: '.' not in param['id'], other_params))
        self.assertEqual(gbl_params, [
            {
                'target': "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='Keq']/@value",
                'group': 'Other parameters',
                'id': 'Keq',
                'name': None,
                'value': 0.32,
                'units': None
            },
        ])

        lcl_params = list(filter(lambda param: param['id'].startswith('SHMT.'), other_params))
        lcl_params.sort(key=lambda param: param['id'])
        self.assertEqual(lcl_params, [
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                           "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Km1']/@value"),
                'group': 'Other parameters',
                'id': 'SHMT.Km1',
                'name': None,
                'value': 1.7,
                'units': None
            },
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                           "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Km2']/@value"),
                'group': 'Other parameters',
                'id': 'SHMT.Km2',
                'name': None,
                'value': 210,
                'units': None
            },
            {
                'target': ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                           "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Vm']/@value"),
                'group': 'Other parameters',
                'id': 'SHMT.Vm',
                'name': None,
                'value': 18330,
                'units': None
            },
        ])

    def test_run_ignore_parameters_set_by_assignment(self):
        filename = 'tests/fixtures/MODEL1904090001-without-comp.sbml-L3V2.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        # initial assignment
        self.assertEqual(next((param for param in model['parameters'] if param['id'] == 'init_concentration_glc'), None), None)

        # assignment rule
        self.assertEqual(next((param for param in model['parameters'] if param['id'] == 'a_sum'), None), None)

    def test_run_file_does_not_exist(self):
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            read_model('__non_existant_file__', format=ModelFormat.sbml)

    def test_run_fbc_framework(self):
        filename = 'tests/fixtures/MODEL1904090001-without-comp.sbml-L3V2.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        params = list(filter(lambda param: param['group'] == 'Other parameters', model['parameters']))
        self.assertEqual(len(params), 9)

        params = list(filter(lambda param: param['group'] == 'Initial compartment sizes', model['parameters']))
        self.assertEqual(len(params), 1)

        params = list(filter(lambda param: param['group'] == 'Initial species amounts/concentrations', model['parameters']))
        self.assertEqual(len(params), 5)

        params = list(filter(lambda param: param['group'] == 'Flux objectives', model['parameters']))
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0], {
            'target': ("/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='atp_consume_max']"
                       "/fbc:listOfFluxObjectives/fbc:fluxObjective[@fbc:reaction='ATPPROD']/@fbc:coefficient"),
            'group': 'Flux objectives',
            'id': 'atp_consume_max/ATPPROD',
            'name': 'Coefficient of atp_consume_max of ATP production',
            'value': 1.0,
            'units': 'dimensionless',
        })

        vars = list(filter(lambda var: var['group'] == 'Objectives', model['variables']))
        self.assertEqual(len(vars), 1)
        self.assertEqual(vars[0], {
            'target': "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='atp_consume_max']",
            'group': 'Objectives',
            'id': 'atp_consume_max',
            'name': 'atp_consume_max',
            'compartment_id': None,
            'compartment_name': None,
            'units': 'millimole / second',
            'constant': False,
            'boundary_condition': False,
        })

        vars = list(filter(lambda var: var['group'] == 'Reaction fluxes', model['variables']))
        self.assertEqual(len(vars), 4)
        var = next(var for var in vars if var['id'] == 'GK')
        self.assertEqual(var, {
            'target': "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='GK']",
            'group': 'Reaction fluxes',
            'id': 'GK',
            'name': 'Glucokinase',
            'compartment_id': None,
            'compartment_name': None,
            'units': 'millimole / second',
            'constant': False,
            'boundary_condition': False,
        })

    def test_run_unsupported_packages(self):
        filename = 'tests/fixtures/MODEL1904090001.sbml-L3V2.xml'
        with self.assertRaisesRegex(ModelIoError, r'package\(s\) are not supported'):
            model = read_model(filename, format=ModelFormat.sbml)

    def test_run_units(self):
        filename = 'tests/fixtures/BIOMD0000000821.sbml-L2V4.xml'
        model = read_model(filename, format=ModelFormat.sbml)
        param = list(filter(lambda param: param['id'] == 'lambda_1', model['parameters']))[0]
        self.assertEqual(param['units'], '1.157 10^-4 1 / second')
