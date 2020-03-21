""" Utilities for working with SED-ML with SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import SedMlGenerator

__all__ = ['SbmlSedMlGenerator']


class SbmlSedMlGenerator(SedMlGenerator):
    """ Generator for SED-ML for SBML models """

    def _add_language_to_model(self, doc_sed, model_sed):
        """ Add a model language to a SED model

        Args:
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            model_sed (:obj:`libsedml.SedModel`): SED model
        """
        self._call_libsedml_method(doc_sed, model_sed, 'setLanguage', 'urn:sedml:sbml')

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
        self._call_libsedml_method(doc_sed, change_sed, 'setTarget',
                                   '/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id="{}"]/@value'.format(
                                       change['parameter']['id']))
        self._call_libsedml_method(doc_sed, change_sed, 'setNewValue', str(change['value']))
        return change_sed

    def _set_var_target(self, id, doc_sed, var_sed):
        """ Set the target of a SED variable

        Args:
            id (:obj:`str`): id
            doc_sed (:obj:`libsedml.SedDocument`): SED document
            var_sed (:obj:`libsedml.SedVariable`): SED: variable
        """
        self._call_libsedml_method(doc_sed, var_sed, 'setTarget',
                                   '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id="{}"]'.format(id))
