from Biosimulations_utils.visualization.escher import escher_to_vega
from jsonschema import validate
import json
import os
import random
import requests
import shutil
import tempfile
import unittest


class EscherVisualizationTestCase(unittest.TestCase):
    ESCHER_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'visualization', 'e_coli_core.Core metabolism.json')

    def setUp(self):
        self.temp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dirname)

    def test_escher_to_vega(self):
        vega_filename = os.path.join(self.temp_dirname, 'vega.json')

        with open(self.ESCHER_FILENAME, 'r') as file:
            map = json.load(file)

        reaction_fluxes = {}
        for reaction in map[1]["reactions"].values():
            reaction_fluxes[reaction['bigg_id']] = random.random() * 2 - 1

        escher_to_vega(self.ESCHER_FILENAME, vega_filename, reaction_fluxes)

        # test that file was created
        self.assertTrue(os.path.isfile(vega_filename))

        # read file (and test that its valid JSON)
        with open(vega_filename, 'r') as file:
            vega = json.load(file)

        # read the Vega schema for the file
        schema_url = vega['$schema']
        response = requests.get(schema_url)
        response.raise_for_status()
        schema = response.json()

        # validate that the file adheres to Vega's schema
        validate(instance=vega, schema=schema)
