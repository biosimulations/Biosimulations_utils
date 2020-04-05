""" Utilities for working with models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format  # noqa: F401
from .data_model import Model, ModelParameter, Variable  # noqa: F401
import abc

__all__ = ['ModelReader', 'ModelIoError', 'ModelIoWarning']


class ModelReader(abc.ABC):
    """ Read information about models """

    def run(self, filename):
        """ Read a model from a file

        Args:
            filename (:obj:`str`): path to a file which defines a model

        Returns:
            :obj:`Model`: model
        """
        model = Model()
        model_orig = self._read_from_file(filename, model)
        self._read_format(model_orig, model)
        self._read_metadata(model_orig, model)
        units = self._read_units(model_orig, model)
        self._read_parameters(model_orig, model, units)
        self._read_variables(model_orig, model, units)

        return model

    @abc.abstractmethod
    def _read_from_file(self, filename, model):
        """ Read a model from a file

        Args:
            filename (:obj:`str`): path to a file which defines a model
            model (:obj:`Model`): model

        Returns:
            :obj:`object`: model encoded in a format such as SBML
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _read_format(self, model_orig, model):
        """ Read the format of a model

        Args:
            model_orig (:obj:`object`): original model encoded in a format such as SBML
            model (:obj:`Model`): model

        Returns:
            :obj:`Format`: format of the model
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _read_metadata(self, model_orig, model):
        """ Read the metadata of a model

        Args:
            model_orig (:obj:`object`): original model encoded in a format such as SBML
            model (:obj:`Model`): model

        Returns:
            :obj:`Model`: model with additional metadata
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _read_units(self, model_orig, model):
        """ Read the units of a model

        Args:
            model_orig (:obj:`object`): original model encoded in a format such as SBML
            model (:obj:`Model`): model

        Returns:
            :obj:`dict`: dictionary that maps the ids of units to their definitions
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _read_parameters(self, model_orig, model):
        """ Read the parameters of a model

        Args:
            model_orig (:obj:`object`): original model encoded in a format such as SBML
            model (:obj:`Model`): model

        Returns:
            :obj:`list` of :obj:`ModelParameter`: information about parameters
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _read_variables(self, model_orig, model):
        """ Read the variables of a model

        Args:
            model_orig (:obj:`object`): original model encoded in a format such as SBML
            model (:obj:`Model`): model

        Returns:
            :obj:`list` of :obj:`Variable`: information about the variables of the model
        """
        pass  # pragma: no cover


class ModelIoError(Exception):
    """ Model IO error """
    pass


class ModelIoWarning(UserWarning):
    """ Model IO warning """
    pass
