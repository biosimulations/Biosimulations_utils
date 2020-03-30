""" Utilities for working with SED-ML with SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .sedml import SedMlSimWriter, SedMlSimReader

__all__ = ['SbmlSedMlSimWriter', 'SbmlSedMlSimReader']

MODEL_LANGUAGE_URN = 'urn:sedml:sbml'
MODEL_LANGUAGE_NAME = 'SBML'


class SbmlSedMlSimWriter(SedMlSimWriter):
    """ Writer for SED-ML for SBML models """
    MODEL_LANGUAGE_URN = MODEL_LANGUAGE_URN
    MODEL_LANGUAGE_NAME = MODEL_LANGUAGE_NAME


class SbmlSedMlSimReader(SedMlSimReader):
    """ Reader for SED-ML for SBML models """
    MODEL_LANGUAGE_URN = MODEL_LANGUAGE_URN
    MODEL_LANGUAGE_NAME = MODEL_LANGUAGE_NAME
