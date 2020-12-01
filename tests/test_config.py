""" Tests of package configuration

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulations_utils import config
import unittest


class ConfigTestCase(unittest.TestCase):
    def test(self):
        self.assertIn('endpoint', config.auth0)
        self.assertIn('endpoint', config.api)
