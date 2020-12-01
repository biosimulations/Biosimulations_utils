""" Tests of REST API client

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulations_utils import api_client
import json
import os
import unittest
import unittest.mock


class ConfigTestCase(unittest.TestCase):
    def test_login_logout_dry_run(self):
        client = api_client.ApiClient(_dry_run=True)
        client.login()
        self.assertEqual(client._device_code, '')
        self.assertEqual(client._auth, {'type': '', 'token': ''})

        client.logout()
        self.assertEqual(client._device_code, None)
        self.assertEqual(client._auth, None)

    @unittest.skipIf(os.getenv('CI', '0') in ['1', 'true'], 'CI does not have credentials to log into BioSimulations')
    def test_login_logout_real(self):
        client = api_client.ApiClient()
        client.login()

        self.assertTrue(client.exec('get', '/hello', response_type=api_client.ResponseType.bytes).startswith('Welcome '))

        client.logout()
        self.assertEqual(client._device_code, None)
        self.assertEqual(client._auth, None)

    @unittest.skipIf(os.getenv('CI', '0') in ['1', 'true'], 'CI does not have credentials to log into BioSimulations')
    def test_complete_example(self):
        # login
        client = api_client.ApiClient()
        client.login()

        # delete models
        response = client.exec('delete', '/models', response_type=api_client.ResponseType.bytes)
        self.assertEqual(response, '')

        # check that there are no models
        response = client.exec('get', '/models')
        self.assertEqual(response, {'data': []})

        # post a model
        with open('tests/fixtures/biomd0000000001.json', 'r') as file:
            model_json = json.load(file)['data']
        response = client.exec('post', '/models', data={'data': model_json})

        # check that the model was posted
        response = client.exec('get', '/models')
        self.assertEqual(len(response['data']), 1)
        model2_json = response['data'][0]

        # check that the stored model is equal to the posted model
        self.assertEqual(model2_json.keys(), model_json.keys())

        for key in model_json['attributes'].keys():
            self.assertEqual(model_json['attributes'][key], model2_json['attributes']
                             [key], "Values of attribute '{}' should be equal".format(key))

        if model2_json['relationships']['parent'] and model2_json['relationships']['parent']['data'] is None:
            model2_json['relationships']['parent'] = None
        model_json['meta']['created'] = model2_json['meta']['created']
        model_json['meta']['updated'] = model2_json['meta']['updated']
        model_json['meta']['version'] = model2_json['meta']['version']

        self.assertEqual(model2_json, model_json)

        # logout
        client.logout()
