""" Tests of utilities for working with SBMl-encoded models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Format, Taxon, Type
from Biosimulations_format_utils.model import ModelFormat, read_model
from Biosimulations_format_utils.model.core import ModelIoError
from Biosimulations_format_utils.model.data_model import Model, Parameter, Variable
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

        # metadata
        self.assertEqual(model.format, Format(
            name='SBML',
            version='L2V4',
            edam_id='format_2585',
            url='http://sbml.org',
        ))

        self.assertEqual(model.framework.name, 'non-spatial continuous framework')

        self.assertEqual(model.taxon, Taxon(
            id=10090,
            name='Mus musculus',
        ))

        # parameters
        gbl_params = list(filter(lambda param: param.group == 'Other global parameters', model.parameters))
        self.assertEqual(len(gbl_params), 1)
        self.assertEqual(gbl_params, [
            Parameter(
                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='parameter_1']/@value",
                group='Other global parameters',
                id='parameter_1',
                name='quantity_1',
                description=None,
                identifiers=[],
                type=Type.float,
                value=0.0,
                recommended_range=[0., 10.],
                units=None
            ),
        ])

        lcl_params = list(filter(lambda param: param.id.startswith('reaction_1/'), model.parameters))
        lcl_params.sort(key=lambda param: param.id)
        self.assertEqual(lcl_params, [
            Parameter(
                target=("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='reaction_1']"
                         "/sbml:kineticLaw/sbml:listOfParameters/sbml:parameter[@id='k1']/@value"),
                group='15 rate constants',
                id='reaction_1/k1',
                name='15: k1',
                description=None,
                identifiers=[],
                type=Type.float,
                value=0.02,
                recommended_range=[0.002, 0.2],
                units=None
            ),
            Parameter(
                target=("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='reaction_1']"
                        "/sbml:kineticLaw/sbml:listOfParameters/sbml:parameter[@id='k2']/@value"),
                group='15 rate constants',
                id='reaction_1/k2',
                name='15: k2',
                description=None,
                identifiers=[],
                type=Type.float,
                value=1.0,
                recommended_range=[0.1, 10.],
                units=None
            ),
        ])

        init_comp_size_params = list(filter(lambda param: param.group == 'Initial compartment sizes', model.parameters))
        self.assertEqual(init_comp_size_params, [Parameter(
            target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='compartment_1']/@size",
            group='Initial compartment sizes',
            id='init_size_compartment_1',
            name='Initial size of compartment',
            description=None,
            identifiers=[],
            type=Type.float,
            value=1.0,
            recommended_range=[0.1, 10.],
            units='10^-3 liter',
        )])

        init_species_params = list(filter(lambda param: param.group == 'Initial species amounts/concentrations', model.parameters))
        init_species_param = next(param for param in init_species_params if param.id == 'init_concentration_species_1')
        self.assertEqual(init_species_param, Parameter(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']/@initialConcentration",
            group='Initial species amounts/concentrations',
            id='init_concentration_species_1',
            name='Initial concentration of MK',
            description=None,
            identifiers=[],
            type=Type.float,
            value=1200.,
            recommended_range=[120., 12000.],
            units=None,
        ))

        # variables
        self.assertEqual(len(model.variables), 24)
        var = next(var for var in model.variables if var.id == 'species_1')
        self.assertEqual(var, Variable(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='species_1']",
            group='Species amounts/concentrations',
            id='species_1',
            name='MK',
            description=None,
            identifiers=[],
            type=Type.float,
            units='10^-6 mole / liter',
        ))

        # errors
        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            read_model(filename, format=ModelFormat.cellml)

    def test_run_l3(self):
        filename = 'tests/fixtures/BIOMD0000000018.sbml-L3V1.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        gbl_params = list(filter(lambda param: param.group == 'Other global parameters', model.parameters))
        self.assertEqual(len(gbl_params), 1)
        self.assertEqual(gbl_params, [
            Parameter(
                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='Keq']/@value",
                group='Other global parameters',
                id='Keq',
                name='Keq',
                description=None,
                identifiers=[],
                type=Type.float,
                value=0.32,
                recommended_range=[0.032, 3.2],
                units=None
            ),
        ])

        lcl_params = list(filter(lambda param: param.id.startswith('SHMT/'), model.parameters))
        lcl_params.sort(key=lambda param: param.id)
        self.assertEqual(lcl_params, [
            Parameter(
                target=("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                         "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Km1']/@value"),
                group='SHMT rate constants',
                id='SHMT/Km1',
                name='SHMT: Km1',
                description=None,
                identifiers=[],
                type=Type.float,
                value=1.7,
                recommended_range=[0.17, 17.],
                units=None
            ),
            Parameter(
                target=("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                        "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Km2']/@value"),
                group='SHMT rate constants',
                id='SHMT/Km2',
                name='SHMT: Km2',
                description=None,
                identifiers=[],
                type=Type.float,
                value=210.,
                recommended_range=[21., 2100.],
                units=None
            ),
            Parameter(
                target=("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='SHMT']"
                        "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='Vm']/@value"),
                group='SHMT rate constants',
                id='SHMT/Vm',
                name='SHMT: Vm',
                description=None,
                identifiers=[],
                type=Type.float,
                value=18330.,
                recommended_range=[1833., 183300.],
                units=None
            ),
        ])

    def test_run_ignore_parameters_set_by_assignment(self):
        filename = 'tests/fixtures/MODEL1904090001-without-comp.sbml-L3V2.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        # initial assignment
        self.assertEqual(next((param for param in model.parameters if param.id == 'init_concentration_glc'), None), None)

        # assignment rule
        self.assertEqual(next((param for param in model.parameters if param.id == 'a_sum'), None), None)

    def test_run_file_does_not_exist(self):
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            read_model('__non_existant_file__', format=ModelFormat.sbml)

    def test_run_fbc_package(self):
        filename = 'tests/fixtures/MODEL1904090001-without-comp.sbml-L3V2.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        params = list(filter(lambda param: param.group == 'Other global parameters', model.parameters))
        self.assertEqual(len(params), 9)

        params = list(filter(lambda param: param.group == 'Initial compartment sizes', model.parameters))
        self.assertEqual(len(params), 1)

        params = list(filter(lambda param: param.group == 'Initial species amounts/concentrations', model.parameters))
        self.assertEqual(len(params), 5)

        params = list(filter(lambda param: param.group == 'Flux objective coefficients', model.parameters))
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0], Parameter(
            target=("/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='atp_consume_max']"
                    "/fbc:listOfFluxObjectives/fbc:fluxObjective[@fbc:reaction='ATPPROD']/@fbc:coefficient"),
            group='Flux objective coefficients',
            id='atp_consume_max/ATPPROD',
            name='Coefficient of atp_consume_max of ATP production',
            description=None,
            identifiers=[],
            type=Type.float,
            value=1.0,
            recommended_range=[0.1, 10.],
            units='dimensionless',
        ))

        vars = list(filter(lambda var: var.group == 'Objectives', model.variables))
        self.assertEqual(len(vars), 1)
        self.assertEqual(vars[0], Variable(
            target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='atp_consume_max']",
            group='Objectives',
            id='atp_consume_max',
            name='atp_consume_max',
            description=None,
            identifiers=[],
            type=Type.float,
            units='millimole / second',
        ))

        vars = list(filter(lambda var: var.group == 'Reaction fluxes', model.variables))
        self.assertEqual(len(vars), 4)
        var = next(var for var in vars if var.id == 'GK')
        self.assertEqual(var, Variable(
            target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='GK']",
            group='Reaction fluxes',
            id='GK',
            name='Glucokinase',
            description=None,
            identifiers=[],
            type=Type.float,
            units='millimole / second',
        ))

    def test_run_multi_package(self):
        filename = 'tests/fixtures/multi_example1.sbml-L3V1.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        self.assertEqual(len(model.parameters), 8)
        param = next(param for param in model.parameters if param.id == 'rc_Intra_Complex_Trans_Association/kon')
        self.assertEqual(param, Parameter(
            target=("/sbml:sbml/sbml:model/sbml:listOfReactions/multi:intraSpeciesReaction[@id='rc_Intra_Complex_Trans_Association']"
                    "/sbml:kineticLaw/sbml:listOfLocalParameters/sbml:localParameter[@id='kon']/@value"),
            group='Intra-Complex_Trans_Association rate constants',
            id='rc_Intra_Complex_Trans_Association/kon',
            name='Intra-Complex_Trans_Association: kon',
            description=None,
            identifiers=[],
            type=Type.float,
            value=100.,
            recommended_range=[10., 1000.],
            units=None,
        ))

    def test_run_qual_package(self):
        filename = 'tests/fixtures/qual_example_4.2.sbml-L3V1.xml'
        model = read_model(filename, format=ModelFormat.sbml)

        self.assertEqual(len(model.parameters), 4)
        param = next(param for param in model.parameters if param.id == 'init_level_A')
        self.assertEqual(param, Parameter(
            target='/' + '/'.join([
                "sbml:sbml",
                "sbml:model",
                "qual:listOfQualitativeSpecies",
                "qual:qualitativeSpecies[@qual:id='A']",
                "@qual:initialLevel",
            ]),
            group='Initial species levels',
            id='init_level_A',
            name='Initial level of A',
            description=None,
            identifiers=[],
            type=Type.integer,
            value=2,
            recommended_range=[0, 2],
            units='dimensionless',
        ))

        self.assertEqual(len(model.variables), 4)
        var = next(var for var in model.variables if var.id == 'A')
        self.assertEqual(var, Variable(
            target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='A']",
            group='Species levels',
            id='A',
            name=None,
            description=None,
            identifiers=[],
            type=Type.integer,
            units='dimensionless',
        ))

    def test_run_unsupported_packages(self):
        filename = 'tests/fixtures/MODEL1904090001.sbml-L3V2.xml'
        with self.assertRaisesRegex(ModelIoError, r'package\(s\) are not supported'):
            model = read_model(filename, format=ModelFormat.sbml)

    def test_run_units(self):
        filename = 'tests/fixtures/BIOMD0000000821.sbml-L2V4.xml'
        model = read_model(filename, format=ModelFormat.sbml)
        param = list(filter(lambda param: param.id == 'lambda_1', model.parameters))[0]
        self.assertEqual(param.units, '1.157 10^-4 1 / second')
