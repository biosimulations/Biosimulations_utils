""" Utilities for working with models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import BiomodelFormat
from .sbml import SbmlBiomodelReader

__all__ = ['read_biomodel']


def read_biomodel(filename, format):
    """ Read a model from a file

    Args:
        filename (:obj:`str`): path to a file which defines a model
        format (:obj:`BiomodelFormat`): model format

    Returns:
        :obj:`dict`: model
    """
    if format == BiomodelFormat.sbml:
        Reader = SbmlBiomodelReader
    else:
        raise NotImplementedError("Model format {} is not supported".format(format.name))
    return Reader().run(filename)
