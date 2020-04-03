""" Tests for importing models from BioModels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-23
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Identifier, JournalReference, License, Person, Taxon
from Biosimulations_format_utils.import_resources import import_models
import libsbml
import shutil
import tempfile
import unittest


class ImportBioModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()
        shutil.rmtree(self.dirname)

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test(self):
        models = import_models.ImportBioModels(_max_models=5, _cache_dir=self.dirname).run()
        self.assertEqual(len(models), 5)

        self.assertEqual(models[0].id, 'BIOMD0000000001')
        self.assertEqual(models[0].name, 'Edelstein1996 - EPSP ACh event')

        self.assertEqual(models[0].file.name, 'BIOMD0000000001_url.xml')
        self.assertEqual(models[0].file.type, 'application/sbml+xml')
        self.assertGreater(models[0].file.size, 0)

        self.assertEqual(models[0].image.name, 'BIOMD0000000001_url.png')
        self.assertEqual(models[0].image.type, 'image/png')
        self.assertGreater(models[0].image.size, 0)

        self.assertEqual(models[0].description,
                         ('<div>\n'
                             '  <p>Model of a nicotinic Excitatory Post-Synaptic Potential in a\n'
                             '  Torpedo electric organ. Acetylcholine is not represented\n'
                             '  explicitely, but by an event that changes the constants of\n'
                             '  transition from unliganded to liganded.\xa0\n'
                             '  <br/></p>\n'
                             '</div>'))
        self.assertEqual(models[0].taxon, Taxon(
            id=7787,
            name="Tetronarce californica",
        ))
        self.assertEqual(models[0].tags, [])
        self.assertEqual(models[0].identifiers, [Identifier(
            namespace="biomodels.db",
            id="BIOMD0000000001",
        )])
        self.assertEqual(models[0].refs, [JournalReference(
            authors="S J Edelstein, O Schaad, E Henry, D Bertrand & J P Changeux",
            title="A kinetic mechanism for nicotinic acetylcholine receptors based on multiple allosteric transitions.",
            journal="Biological cybernetics",
            volume="75",
            num=None,
            pages="361-379",
            year=1996,
            doi="10.1007/s004220050302",
        )])
        self.assertEqual(len(models[0].authors), 5)
        self.assertEqual(models[0].authors[0], Person(
            last_name="Edelstein",
            first_name="S",
            middle_name="J"
        ))
        self.assertEqual(models[0].license, License.cc0)
