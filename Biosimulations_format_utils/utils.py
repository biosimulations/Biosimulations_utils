""" Utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import math
import pint

__all__ = ['unit_registry', 'pretty_print_units']

unit_registry = pint.UnitRegistry()


def pretty_print_units(units_str):
    """ Pretty print units

    Args:
        units_str (:obj:`str`): units

    Returns:
        :obj:`str`: pretty printed units
    """
    try:
        exp = unit_registry.parse_expression(units_str)
    except pint.errors.UndefinedUnitError:
        return None
    mag = exp.magnitude
    pow = math.floor(math.log10(mag))
    mag = round(mag / math.pow(10, pow), 3)
    units = str(exp.units)

    if pow == 0:
        if mag == 1:
            return units
        else:
            return '{} {}'.format(mag, units)
    else:
        if mag == 1:
            return '10^{} {}'.format(pow, units)
        else:
            return '{} 10^{} {}'.format(mag, pow, units)


def assert_exception(success, exception):
    """ Raise an error if :obj:`success` is :obj:`False`

    Args:
        success (:obj:`bool`)
        exception (:obj:`Exception`)

    Raises:
        :obj:`Exception`
    """
    if not success:
        raise exception
