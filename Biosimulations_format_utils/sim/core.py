""" Utilities for working with simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc

__all__ = ['SimWriter', 'SimReader', 'SimIoError', 'SimIoWarning']


class SimWriter(abc.ABC):
    pass


class SimReader(abc.ABC):
    @staticmethod
    def _assert(success, message='Operation failed'):
        """ Raise an error if :obj:`success` is :obj:`False`

        Args:
            success (:obj:`bool`)
            message (:obj:`str`, optional): error message

        Raises:
            :obj:`SimIoError`
        """
        if not success:
            raise SimIoError(message)


class SimIoError(Exception):
    """ Simulation IO error """
    pass


class SimIoWarning(UserWarning):
    """ Simulation IO warning """
    pass
