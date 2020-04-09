""" Utilities for working with models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import ModelFormat
from .sbml import SbmlModelReader

__all__ = ['read_model']


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
