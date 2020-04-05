""" Tests for importing models from BioModels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-23
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Identifier, JournalReference, License, Person, Taxon
from Biosimulations_format_utils.import_resources import biomodels
from Biosimulations_format_utils.model.data_model import Model
from Biosimulations_format_utils.sim.data_model import Simulation
import mock
import shutil
import tempfile
import unittest


class BioModelsImporterTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()
        shutil.rmtree(self.dirname)

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test(self):
        importer = biomodels.BioModelsImporter(_max_models=6, _cache_dir=self.dirname)
        return_value = {
            'matches': 925,
            'models': [
                {'id': 'BIOMD0000000001', 'name': 'Edelstein1996 - EPSP ACh event'},
                {'id': 'BIOMD0000000002', 'name': 'Edelstein1996 - EPSP ACh species'},
                {'id': 'BIOMD0000000003', 'name': 'Goldbeter1991 - Min Mit Oscil'},
                {
                    'id': 'BIOMD0000000297',  # has time course simulation
                    'name': 'Ciliberto2003_Morphogenesis_Checkpoint',
                },
                {
                    'id': 'BIOMD0000000643',  # has time course and steady state simulations
                    'name': 'Musante2017 - Switching behaviour of PP2A inhibition by ARPP-16 - mutual inhibitions',
                },
                {'id': 'BIOMD0000000075', 'name': 'Xu2003 - Phosphoinositide turnover'},  # unable to generate image
                {'id': 'BIOMD0000000007', 'name': 'Novak1997 - Cell Cycle'},
                {'id': 'BIOMD0000000008', 'name': 'Gardner1998 - Cell Cycle Goldbeter'},
                {'id': 'BIOMD0000000009', 'name': 'Huang1996 - Ultrasensitivity in MAPK cascade'},
                {
                    'id': 'BIOMD0000000010',
                    'name': 'Kholodenko2000 - Ultrasensitivity and negative feedback bring oscillations in MAPK cascade',
                },
            ],
        }
        with mock.patch.object(biomodels.BioModelsImporter, 'get_model_batch', return_value=return_value):
            models, sims, stats = importer.run()
        self.assertEqual(len(models), 6)

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

        self.assertEqual(stats, {
            'models': {
                'total': 6,
                'frameworks': {
                    'non-spatial continuous framework': 6,
                },
                'layouts': 0,
                'taxa': {
                    'Amphibia': 1,
                    'Tetronarce californica': 2,
                    'Schizosaccharomyces pombe': 1,
                    'Mus musculus': 1,
                    'Mus sp.': 1,
                },
                'simulated': 2,
            },
            'sims': {
                'total': 3,
                'time course': 2,
                'one step': 0,
                'steady-state': 1,
            }
        })

        for model in models:
            self.assertEqual(Model.from_json(model.to_json()), model)
        for sim in sims:
            self.assertEqual(Simulation.from_json(sim.to_json()), sim)

        models_2, sims_2, stats_2 = importer.read_data()
        for model, model_2 in zip(models, models_2):
            self.assertEqual(model_2, model)
        for sim, sim_2 in zip(sims, sims_2):
            self.assertEqual(sim_2, sim)
        self.assertEqual(stats_2, stats)
