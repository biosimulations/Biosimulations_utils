""" Utilities for working with simulation experiments

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import SimFormat
from ..model.data_model import ModelFormat
from ..visualization.data_model import Visualization  # noqa: F401
from .sbml import SbmlSedMlSimWriter, SbmlSedMlSimReader

__all__ = ['write_sim', 'read_sim']


def write_sim(model_vars, sim, model_filename, sim_filename, sim_format, **sim_format_opts):
    """ Write a simulation experiment to a file

    Args:
        model_vars (:obj:`list` of :obj:`dict`): List of variables in the model. Each variable should have the keys `id` and `target`.
        sim (:obj:`dict`): Simulation experiment
        model_filename (:obj:`str`): Path to the model definition
        sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
        sim_format (:obj:`SimFormat`): simulation experiment format
        sim_format_opts (:obj:`dict`): options to the simulation experiment format (e.g., level, version)
    """
    model_format = ModelFormat[sim.model.format.name]
    if sim_format == SimFormat.sedml:
        if model_format == ModelFormat.sbml:
            Writer = SbmlSedMlSimWriter
        else:
            raise NotImplementedError('Model format {} is not supported'.format(model_format.name))
    else:
        raise NotImplementedError("Simulation experiment format {} is not supported".format(sim_format.name))
    return Writer().run(model_vars, sim, model_filename, sim_filename, **sim_format_opts)


def read_sim(filename, model_format, sim_format):
    """ Read a simulation experiment from a file

    Args:
        filename (:obj:`str`): path to save simulation
        model_format (:obj:`ModelFormat`): model format
        sim_format (:obj:`SimFormat`): simulation experiment format

    Returns:
        :obj:`list` of :obj:`Simulation`: simulations
        :obj:`Visualization`: visualization
    """
    if sim_format == SimFormat.sedml:
        if model_format == ModelFormat.sbml:
            Reader = SbmlSedMlSimReader
        else:
            raise NotImplementedError('Model format {} is not supported'.format(model_format.name))
    else:
        raise NotImplementedError("Simulation experiment format {} is not supported".format(sim_format.name))
    return Reader().run(filename)
