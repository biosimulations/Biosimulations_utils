""" Utilities for working with simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc

__all__ = ['SimulationWriter', 'SimulationReader', 'SimulationIoError', 'SimulationIoWarning']


class SimulationWriter(abc.ABC):
    """ Base class for simulation writers """
    pass


class SimulationReader(abc.ABC):
    """ Base class for simulation readers """
    pass


class SimulationIoError(Exception):
    """ Simulation IO error """
    pass


class SimulationIoWarning(UserWarning):
    """ Simulation IO warning """
    pass
