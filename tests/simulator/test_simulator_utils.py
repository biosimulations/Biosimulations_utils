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


class UtilsTestCase(unittest.TestCase):
    @unittest.skipIf(docker is None, 'Docker not available')
    def test(self):
        validator = SimulatorValidator()
        valid_examples, invalid_examples = validator.run('crbm/biosimulations_tellurium', 'tests/fixtures/tellurium-properties.json')
        # TODO: update once tellurium fixed; tellurium fails on data generator for Mcmin
        self.assertEqual(
            set([ex.filename for ex in valid_examples]),
            set([
                'BIOMD0000000297.omex',
                'BIOMD0000000734.omex',
            ]),
        )
        self.assertEqual(
            set([ex.test_case.filename for ex in invalid_examples]),
            set([
                'BIOMD0000000297.xml',
            ])
        )
