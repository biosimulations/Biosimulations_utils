""" Utilities for working with simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc

__all__ = ['SimWriter', 'SimReader', 'SimIoError', 'SimIoWarning']


class SimWriter(abc.ABC):
    """ Base class for simulation writers """
    pass


class SimReader(abc.ABC):
    """ Base class for simulation readers """
    pass


class SimIoError(Exception):
    """ Simulation IO error """
    pass


class SimIoWarning(UserWarning):
    """ Simulation IO warning """
    pass
