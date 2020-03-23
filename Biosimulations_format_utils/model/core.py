""" Utilities for working with models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc

__all__ = ['ModelReader']


class ModelReader(abc.ABC):
    """ Read information about models """

    def run(self, filename):
        """ Read a model from a file

        Args:
            filename (:obj:`str`): path to a file which defines a model

        Returns:
            :obj:`dict`: model
        """
        model_orig = self._read_from_file(filename)

        model = {}
        self._read_units(model_orig, model)
        self._read_parameters(model_orig, model)

        return model

    @abc.abstractmethod
    def _read_from_file(self, filename):
        """ Read a model from a file

        Args:
            filename (:obj:`str`): path to a file which defines a model

        Returns:
            :obj:`object`: model encoded in a format such as SBML
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _read_units(self, model_orig, model):
        """ Read the units of a model

        Args:
            model_orig (:obj:`object`): original model encoded in a format such as SBML
            model (:obj:`dict`): model
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _read_parameters(self, model_orig, model):
        """ Read the parameters of a model

        Args:
            model_orig (:obj:`object`): original model encoded in a format such as SBML
            model (:obj:`dict`): model
        """
        pass  # pragma: no cover
