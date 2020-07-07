""" Tests of utilities for generating and executing COMBINE archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-10
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils import config
from Biosimulations_utils.archive.data_model import ArchiveFormat
from Biosimulations_utils.biomodel.data_model import BiomodelingFramework, BiomodelFormat
from Biosimulations_utils.simulation.data_model import SimulationFormat
try:
    from Biosimulations_utils.simulator.testing import SimulatorValidator, TestCase, TestCaseType
except ModuleNotFoundError:
    pass
try:
    import docker
except ModuleNotFoundError:
    docker = None
import os
import unittest


@unittest.skipIf(docker is None, 'Docker not available')
class UtilsTestCase(unittest.TestCase):
    def test_init(self):
        validator = SimulatorValidator()

        self.assertGreaterEqual(len(validator.test_cases), 4)

        test_case = next(test_case for test_case in validator.test_cases if test_case.id == 'BIOMD0000000297.omex')
        self.assertEqual(test_case, TestCase(
            id='BIOMD0000000297.omex',
            filename=os.path.join(config.combine_test_suite.dirname, 'BIOMD0000000297.omex'),
            type=TestCaseType.archive,
            modeling_framework=BiomodelingFramework.non_spatial_continuous,
            model_format=BiomodelFormat.sbml,
            simulation_format=SimulationFormat.sedml,
            archive_format=ArchiveFormat.combine,
        ))

    def test_run(self):
        validator = SimulatorValidator()
        valid_cases, case_exceptions, skipped_cases = validator.run(
            'crbm/biosimulations_tellurium', 'tests/fixtures/tellurium-properties.json')
        # TODO: update once tellurium fixed; tellurium fails on data generator for Mcmin
        self.assertEqual(
            set([case.id for case in valid_cases]),
            set([
                'BIOMD0000000297.omex',
                'BIOMD0000000734.omex',
            ]),
        )
        self.assertEqual(
            set([case_exception.test_case.id for case_exception in case_exceptions]),
            set([
                'BIOMD0000000297.xml',
            ])
        )
        self.assertGreater(len(skipped_cases), 0)

    def test_skip_case(self):
        validator = SimulatorValidator()
        valid_cases, case_exceptions, skipped_cases = validator.run(
            'crbm/biosimulations_tellurium', 'tests/fixtures/tellurium-properties.json', test_case_ids=[
                'BIOMD0000000297.omex',
            ])
        self.assertEqual(
            set([case.id for case in valid_cases]),
            set([
                'BIOMD0000000297.omex',
            ]),
        )
        self.assertEqual(case_exceptions, [])
        self.assertGreater(len(skipped_cases), 2)
