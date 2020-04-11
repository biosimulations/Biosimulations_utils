""" Utilities for working with simulation experiments

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import SimulationFormat
from ..visualization.data_model import Visualization  # noqa: F401
from .sedml import SedMlSimulationWriter, SedMlSimulationReader

__all__ = ['write_simulation', 'read_simulation']


def write_simulation(sim, filename, format, **format_opts):
    """ Write a simulation experiment to a file

    Args:
        sim (:obj:`dict`): Simulation experiment
        filename (:obj:`str`): Path to save simulation experiment in SED-ML format
        format (:obj:`SimulationFormat`): simulation experiment format
        format_opts (:obj:`dict`): options to the simulation experiment format (e.g., level, version)
    """
    if format == SimulationFormat.sedml:
        Writer = SedMlSimulationWriter
    else:
        raise NotImplementedError("Simulation experiment format {} is not supported".format(format.name))
    return Writer().run(sim, filename, **format_opts)


def read_simulation(filename, format):
    """ Read a simulation experiment from a file

    Args:
        filename (:obj:`str`): path to save simulation
        format (:obj:`SimulationFormat`): simulation experiment format

    Returns:
        :obj:`list` of :obj:`Simulation`: simulations
        :obj:`Visualization`: visualization
    """
    if format == SimulationFormat.sedml:
        Reader = SedMlSimulationReader
    else:
        raise NotImplementedError("Simulation experiment format {} is not supported".format(format.name))
    return Reader().run(filename)
