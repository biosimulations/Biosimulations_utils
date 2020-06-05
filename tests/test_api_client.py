""" Tests of REST API client

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils import api_client
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

    def test_login_logout(self):
        client = api_client.ApiClient(_dry_run=True)
        client.login()
        self.assertEqual(client._device_code, '')
        self.assertEqual(client._auth, {'type': '', 'token': ''})
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

        id = 'api-client-test-model'
        name = 'API client test model'
        owner = 'jonrkarr'

        response = client.exec('put', '/models/' + id, data={
            'id': id,
            'owner': owner,
        })
        assert response['name'] is None

        response = client.exec('get', '/models/' + id)
        assert response['name'] is None

        response = client.exec('put', '/models/' + id, data={
            'id': id,
            'owner': owner,
            'name': name
        })
        assert response['name'] == name

        response = client.exec('get', '/models/' + id)
        assert response['name'] == name

        # logout
        client.logout()
