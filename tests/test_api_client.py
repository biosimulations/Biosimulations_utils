""" Tests of REST API client

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils import api_client
import json
import os
import unittest
import unittest.mock


class ConfigTestCase(unittest.TestCase):
    @unittest.skip('API under development')
    def test_get_models(self):
        client = api_client.ApiClient()
        response = client.exec('get', '/models')
        self.assertIsInstance(response, list)
        self.assertIsInstance(response[0], dict)
        self.assertIn('id', response[0])
        self.assertIn('owner', response[0])
        self.assertIn('created', response[0])

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

        self.assertEqual(client.exec('get', '/hello', response_type=api_client.ResponseType.bytes), 'jonrkarr')

        client.logout()
        self.assertEqual(client._device_code, None)
        self.assertEqual(client._auth, None)

    @unittest.skip('API under development')
    def test_put(self):
        client = api_client.ApiClient(_dry_run=True)
        client._auth = {'type': 'bearer', 'token': 'ZZZ'}
        result = client.exec('post', '/models/new-model', {
            'id': 'new-model',
        })
        self.assertEqual(result, None)

    @unittest.skipIf(os.getenv('CI', '0') in ['1', 'true'], 'CI does not have credentials to log into BioSimulations')
    def test_complete_example(self):
        client = api_client.ApiClient()
        client.login()

        response = client.exec('delete', '/models', response_type=api_client.ResponseType.bytes)
        self.assertEqual(response, '')

        response = client.exec('get', '/models')
        self.assertEqual(response, [])

        with open('tests/fixtures/model.json', 'r') as file:
            model = json.load(file)
        response = client.exec('post', '/models', data=model)

        response = client.exec('get', '/models')
        self.assertEqual(len(response), 1)
        model2 = response[0]
        model2.pop('_id')
        model2.pop('__v')
        model['data'].pop('type')
        model['data']['owner'] = model['data']['relationships']['owner']['data']['id']
        model['data']['file'] = model['data']['relationships']['file']['data']['id']
        # model['data']['image'] = model['data']['relationships']['image']['data']['id']
        model['data']['parent'] = model['data']['relationships']['parent']['data']['id']
        model['data'].pop('relationships')

        for key in model['data'].keys():
            self.assertEqual(response[0][key], model['data'][key])

        self.assertEqual(response[0], model['data'])

        # logout
        client.logout()
