""" Utilities for working with simulation experiments

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..model import ModelFormat
from .sbml import SbmlSedMlSimWriter, SbmlSedMlSimReader
import wc_utils.util.enumerate

__all__ = ['SimFormat', 'write_sim', 'read_sim']


class SimFormat(int, wc_utils.util.enumerate.CaseInsensitiveEnum):
    """ Simulation experiment formats """
    SEDML = 1  # SED-ML
    SESSL = 2  # SESSL


def write_sim(model_species, sim, model_filename, sim_filename, sim_format, **sim_format_opts):
    """ Write a simulation experiment to a file

    Args:
        model_species (:obj:`list` of :obj:`dict`): List of species in the model. Each species should have the key `id`
        sim (:obj:`dict`): Simulation experiment
        model_filename (:obj:`str`): Path to the model definition
        sim_filename (:obj:`str`): Path to save simulation experiment in SED-ML format
        sim_format (:obj:`SimFormat`): simulation experiment format
        sim_format_opts (:obj:`dict`): options to the simulation experiment format (e.g., level, version)
    """
    model_format = ModelFormat[sim['model']['format']['name']]
    if sim_format == SimFormat.sedml:
        if model_format == ModelFormat.sbml:
            Writer = SbmlSedMlSimWriter
        else:
            raise NotImplementedError('Model format {} is not supported'.format(model_format.name))
    else:
        raise NotImplementedError("Simulation experiment format {} is not supported".format(sim_format.name))
    return Writer().run(model_species, sim, model_filename, sim_filename, **sim_format_opts)


def read_sim(filename, model_format, sim_format):
    """ Read a simulation experiment from a file

    Args:        
        filename (:obj:`str`): path to save simulation
        model_format (:obj:`ModelFormat`): model format
        sim_format (:obj:`SimFormat`): simulation experiment format

    Returns:
        :obj:`list` of :obj:`dict`: List of species in the model. Each species should have the key `id`
        :obj:`dict`: Simulation experiment
        :obj:`str`: Path to the model definition
        :obj:`dict`: simulation experiment format options (e.g., level, version)
    """
    if sim_format == SimFormat.sedml:
        if model_format == ModelFormat.sbml:
            Reader = SbmlSedMlSimReader
        else:
            raise NotImplementedError('Model format {} is not supported'.format(model_format.name))
    else:
        raise NotImplementedError("Simulation experiment format {} is not supported".format(sim_format.name))
    return Reader().run(filename)
