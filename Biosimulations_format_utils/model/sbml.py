""" Utilities for working with SBML-encoded models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-22
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import ModelReader
import libsbml

__all__ = ['SbmlModelReader']


class SbmlModelReader(ModelReader):
    """ Read information about SBML-encoded models """

    def _read_from_file(self, filename):
        """ Read a SBML-encoded model from a file

        Args:
            filename (:obj:`str`): path to a file which defines an SBML-encoded model

        Returns:
            :obj:`libsbml.Model`: SBML-encoded model
        """
        reader = libsbml.SBMLReader()
        doc = reader.readSBMLFromFile(filename)
        return doc.getModel()

    def _read_parameters(self, model_sbml, model):
        """ Reader information about the parameters of a model

        Args:
            model_sbml (:obj:`libsbml.Model`): SBML-encoded model
            model (:obj:`dict`): model

        Returns:
            :obj:`list` of :obj:`dict`: information about parameters
        """
        model['parameters'] = parameters = []

        for i_param in range(model_sbml.getNumParameters()):
            param_sbml = model_sbml.getParameter(i_param)
            parameters.append(self._read_parameter(param_sbml))

        for i_rxn in range(model_sbml.getNumReactions()):
            rxn_sbml = model_sbml.getReaction(i_rxn)
            kin_law_sbml = rxn_sbml.getKineticLaw()
            if not kin_law_sbml:
                continue

            reaction_id = rxn_sbml.getId() or None
            reaction_name = rxn_sbml.getName() or None

            for i_param in range(kin_law_sbml.getNumParameters()):
                param_sbml = kin_law_sbml.getParameter(i_param)
                parameters.append(self._read_parameter(param_sbml, reaction_id=reaction_id, reaction_name=reaction_name))

            for i_param in range(kin_law_sbml.getNumLocalParameters()):
                param_sbml = kin_law_sbml.getLocalParameter(i_param)
                parameters.append(self._read_parameter(param_sbml, reaction_id=reaction_id, reaction_name=reaction_name))

        return parameters

    def _read_parameter(self, param_sbml, reaction_id=None, reaction_name=None):
        """ Read information about a SBML parameter

        Args:
            param_sbml (:obj:`libsbml.Parameter`): SBML parameter
            reaction_id (:obj:`str`, optional): id of the parent reaction (used by local parameters)
            reaction_name (:obj:`str`, optional): name of the parent reaction (used by local parameters)

        Returns:
            :obj:`dict`: information about the parameter
        """
        return {
            'reaction_id': reaction_id,
            'id': param_sbml.getId() or None,
            'reaction_name': reaction_name,
            'name': param_sbml.getName() or None,
            'value': param_sbml.getValue(),
            'units': param_sbml.getUnits() or None,
        }
