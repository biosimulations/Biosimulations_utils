""" Utilities for working with SED-ML with SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import SedMlWriter, SedMlReader
import libsedml
import re

__all__ = ['SbmlSedMlWriter', 'SbmlSedMlReader']

MODEL_LANGUAGE_URN = 'urn:sedml:sbml'
MODEL_LANGUAGE_NAME = 'SBML'


class SbmlSedMlWriter(SedMlWriter):
    """ Writer for SED-ML for SBML models """
    MODEL_LANGUAGE_URN = MODEL_LANGUAGE_URN
    MODEL_LANGUAGE_NAME = MODEL_LANGUAGE_NAME

    def _add_parameter_change_to_model(self, change, doc_sed, model_sed):
        """ Add a model parameter change to a SED document

        Args:
            change (:obj:`dict`): model parameter change
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model

        Returns:
            :obj:`libsedml.SedChangeAttribute`: SED model parameter change
        """
        change_sed = model_sed.createChangeAttribute()
        if change['parameter'].get('reactionId', None):
            self._call_libsedml_method(
                doc_sed, change_sed, 'setTarget', '/'.join([
                    '/sbml:sbml',
                    'sbml:model',
                    'sbml:listOfReactions',
                    'sbml:reaction[@id="{}"]'.format(change['parameter']['reactionId']),
                    'sbml:kineticLaw',
                    'sbml:listOfLocalParameters',
                    'sbml:localParameter[@id="{}"]'.format(change['parameter']['id']),
                    '@value',
                ]))
        else:
            self._call_libsedml_method(
                doc_sed, change_sed, 'setTarget', '/'.join([
                    '/sbml:sbml',
                    'sbml:model',
                    'sbml:listOfParameters',
                    'sbml:parameter[@id="{}"]'.format(change['parameter']['id']),
                    '@value',
                ]))
        self._add_annotation_to_obj({'name': change['parameter']['name']}, doc_sed, change_sed)
        self._call_libsedml_method(doc_sed, change_sed, 'setNewValue', str(change['value']))
        return change_sed

    def _set_var_target(self, id, doc_sed, var_sed):
        """ Set the target of a SED variable

        Args:
            id (:obj:`str`): id
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            var_sed (:obj:`libsedml.SedVariable`): SED: variable
        """
        self._call_libsedml_method(
            doc_sed, var_sed, 'setTarget',
            '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id="{}"]'.format(id))


class SbmlSedMlReader(SedMlReader):
    """ Reader for SED-ML for SBML models """
    MODEL_LANGUAGE_URN = MODEL_LANGUAGE_URN
    MODEL_LANGUAGE_NAME = MODEL_LANGUAGE_NAME

    def _get_parameter_change_from_model(self, change_sed):
        """ Get a model parameter change from a SED change attribute

        Args:
            change_sed (:obj:`libsedml.SedChangeAttribute`): SED change attribute

        Returns:
            obj:`dict`: model parameter change
        """
        target = change_sed.getTarget()

        match = re.search(r'/sbml:parameter\[@id="(.*?)"\]/', target)
        if match:
            reactionId = None
            id = match.group(1)
        else:
            match = re.search(r'/sbml:reaction\[@id="(.*?)"\]/', target)
            reactionId = match.group(1)

            match = re.search(r'/sbml:localParameter\[@id="(.*?)"\]/', target)
            id = match.group(1)

        props = self._get_obj_annotation(change_sed)

        return {
            "parameter": {
                "id": id,
                "reactionId": reactionId,
                "name": props.get('name', None),
            },
            "value": float(change_sed.getNewValue())
        }
