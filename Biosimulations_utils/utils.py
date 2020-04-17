""" Utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import logging
import math
import os
import pint

__all__ = ['get_enum_format_by_attr', 'unit_registry', 'pretty_print_units', 'assert_exception', 'logger']


def get_enum_format_by_attr(FormatEnum, attr_name, attr_val):
    """ Get a biomodel format by its specification URL

    Args:
        FormatEnum (:obj:`type`): enumeration of formats (i.e. subclass of :obj:`enum.Enum`)
        attr_name (:obj:`str`): attribute name
        attr_val (:obj:`str`): attribute value

    Returns:
        :obj:`Format`: format
    """
    for format in FormatEnum.__members__.values():
        if getattr(format.value, attr_name) == attr_val:
            return format.value


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
        if pow == -24:
            pow_str = 'y'
        elif pow == -21:
            pow_str = 'z'
        elif pow == -18:
            pow_str = 'a'
        elif pow == -15:
            pow_str = 'f'
        elif pow == -12:
            pow_str = 'p'
        elif pow == -9:
            pow_str = 'n'
        elif pow == -6:
            pow_str = 'µ'
        elif pow == -3:
            pow_str = 'm'
        elif pow == -2:
            pow_str = 'c'
        elif pow == -1:
            pow_str = 'd'
        elif pow == 1:
            pow_str = 'da'
        elif pow == 2:
            pow_str = 'h'
        elif pow == 3:
            pow_str = 'k'
        elif pow == 6:
            pow_str = 'M'
        elif pow == 9:
            pow_str = 'G'
        elif pow == 12:
            pow_str = 'T'
        elif pow == 15:
            pow_str = 'P'
        elif pow == 18:
            pow_str = 'E'
        elif pow == 21:
            pow_str = 'Z'
        elif pow == 24:
            pow_str = 'Y'
        else:
            pow_str = '10^{} '.format(pow)

        if mag == 1:
            return '{}{}'.format(pow_str, units)
        else:
            return '{} {}{}'.format(mag, pow_str, units)


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


def create_logger():
    """ Create a logger

    Returns:
        :obj:`logging.Logger`: logger
    """
    formatter = logging.Formatter('-'.join([
        '%(levelname)s',
        '%(pathname)s',
        '%(funcName)s',
        '%(lineno)d',
        '%(message)s',
    ]))

    handler = logging.FileHandler(os.path.expanduser('~/.cache/Biosimulations_utils/log.log'))
    handler.setFormatter(formatter)

    logger = logging.getLogger('biosimulations_utils')
    logger.addHandler(handler)

    return logger


logger = create_logger()
