""" Tests of utility methods

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulations_utils.biomodel.data_model import BiomodelFormat
from biosimulations_utils.utils import (get_enum_format_by_attr, pretty_print_units, assert_exception,
                                        datetime_to_time_since_epoch, time_since_epoch_to_datetime)
import unittest


class UtilsTestCase(unittest.TestCase):
    def test_get_enum_format_by_attr(self):
        self.assertEqual(get_enum_format_by_attr(BiomodelFormat, 'sed_urn', 'urn:sedml:language:sbml'), BiomodelFormat.sbml.value)

    def test_pretty_print_units(self):
        self.assertEqual(pretty_print_units('undefined'), None)
        self.assertEqual(pretty_print_units('s'), 'second')
        self.assertEqual(pretty_print_units('2 s'), '2.0 second')
        self.assertEqual(pretty_print_units('10 s'), 'dasecond')
        self.assertEqual(pretty_print_units('20 s'), '2.0 dasecond')

        self.assertEqual(pretty_print_units('10^-24 s'), 'ysecond')
        self.assertEqual(pretty_print_units('10^-21 s'), 'zsecond')
        self.assertEqual(pretty_print_units('10^-18 s'), 'asecond')
        self.assertEqual(pretty_print_units('10^-15 s'), 'fsecond')
        self.assertEqual(pretty_print_units('10^-12 s'), 'psecond')
        self.assertEqual(pretty_print_units('10^-9 s'), 'nsecond')
        self.assertEqual(pretty_print_units('10^-6 s'), 'µsecond')
        self.assertEqual(pretty_print_units('10^-3 s'), 'msecond')
        self.assertEqual(pretty_print_units('10^-2 s'), 'csecond')
        self.assertEqual(pretty_print_units('10^-1 s'), 'dsecond')
        self.assertEqual(pretty_print_units('10^1 s'), 'dasecond')
        self.assertEqual(pretty_print_units('10^2 s'), 'hsecond')
        self.assertEqual(pretty_print_units('10^3 s'), 'ksecond')
        self.assertEqual(pretty_print_units('10^6 s'), 'Msecond')
        self.assertEqual(pretty_print_units('10^9 s'), 'Gsecond')
        self.assertEqual(pretty_print_units('10^12 s'), 'Tsecond')
        self.assertEqual(pretty_print_units('10^15 s'), 'Psecond')
        self.assertEqual(pretty_print_units('10^18 s'), 'Esecond')
        self.assertEqual(pretty_print_units('10^21 s'), 'Zsecond')
        self.assertEqual(pretty_print_units('10^24 s'), 'Ysecond')

    def test_assert_exception(self):
        assert_exception(True, Exception('message'))
        with self.assertRaisesRegex(Exception, 'message'):
            assert_exception(False, Exception('message'))

    def test_datetime_to_from_time_since_epoch(self):
        sec_since_epoch = 1593377284
        milliseconds_since_epoch = sec_since_epoch * 1e3
        self.assertEqual(datetime_to_time_since_epoch(time_since_epoch_to_datetime(milliseconds_since_epoch)), milliseconds_since_epoch)
