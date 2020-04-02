""" Tests of utility methods

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.utils import pretty_print_units
import unittest


class UtilsModelTestCase(unittest.TestCase):
    def test_pretty_print_units(self):
        self.assertEqual(pretty_print_units('undefined'), None)
        self.assertEqual(pretty_print_units('s'), 'second')
        self.assertEqual(pretty_print_units('2 s'), '2.0 second')
        self.assertEqual(pretty_print_units('10 s'), '10^1 second')
        self.assertEqual(pretty_print_units('20 s'), '2.0 10^1 second')
