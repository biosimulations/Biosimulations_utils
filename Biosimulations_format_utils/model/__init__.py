""" Utilities for working with models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .sbml import SbmlModelReader
import wc_utils.util.enumerate

__all__ = ['ModelFormat', 'read_model']


class ModelFormat(int, wc_utils.util.enumerate.CaseInsensitiveEnum):
    """ Model format """
    BNGL = 1  # BNGL
    CellML = 2  # CellML
    Kappa = 3  # Kappa
    MML = 4  # Multiscale Modeling Language
    NeuroML = 5  # NeuroML
    pharmML = 6  # pharmML
    SBML = 7  # SBML


def read_model(filename, format):
    """ Read a model from a file

    Args:
        filename (:obj:`str`): path to a file which defines a model
        format (:obj:`ModelFormat`): model format

    Returns:
        :obj:`dict`: model
    """
    if format == ModelFormat.sbml:
        Reader = SbmlModelReader
    else:
        raise NotImplementedError("Model format {} is not supported".format(format.name))
    return Reader().run(filename)
