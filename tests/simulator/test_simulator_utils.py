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
import os
import unittest


class UtilsTestCase(unittest.TestCase):
    @unittest.skipIf(os.getenv('CI', '0') in ['1', 'true'], 'Docker not setup in CI')
    def test(self):
        validator = SimulatorValidator()
        valid_examples, invalid_examples = validator.run('crbm/biosimulations_tellurium', 'tests/fixtures/tellurium-properties.json')
        self.assertEqual(
            set([ex.filename for ex in valid_examples]),
            set([
                'BIOMD0000000297.omex',
                'BIOMD0000000297.xml'
            ]),
        )
        self.assertEqual(invalid_examples, [])
