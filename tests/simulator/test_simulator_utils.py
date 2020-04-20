""" Tests of utilities for generating and executing COMBINE archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-10
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

try:
    from Biosimulations_utils.simulator.testing import SimulatorValidator
except ModuleNotFoundError:
    pass
try:
    import docker
except ModuleNotFoundError:
    docker = None
import unittest


@unittest.skipIf(docker is None, 'Docker not available')
class UtilsTestCase(unittest.TestCase):
    def test(self):
        validator = SimulatorValidator()
        valid_cases, case_exceptions, skipped_cases = validator.run(
            'crbm/biosimulations_tellurium', 'tests/fixtures/tellurium-properties.json')
        # TODO: update once tellurium fixed; tellurium fails on data generator for Mcmin
        self.assertEqual(
            set([case.filename for case in valid_cases]),
            set([
                'BIOMD0000000297.omex',
                'BIOMD0000000734.omex',
            ]),
        )
        self.assertEqual(
            set([case_exception.test_case.filename for case_exception in case_exceptions]),
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
            set([case.filename for case in valid_cases]),
            set([
                'BIOMD0000000297.omex',
            ]),
        )
        self.assertEqual(case_exceptions, [])
        self.assertGreater(len(skipped_cases), 2)
