""" Client for interacting with the `BioSimulations REST API <https://api.biosimulations.dev>`_

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from . import config
from unittest import mock
import collections
import click
import enum
import requests
import webbrowser


class ResponseType(int, enum.Enum):
    """ API response type """
    json = 1
    bytes = 2
    other = 3


class ApiClient(object):
    """ Client for interacting with the `BioSimulations REST API <https://api.biosimulations.dev>`_

    Attributes:
        config (:obj:`object`): package configuration
        _dry_run (:obj:`bool`): if :obj:`True`, do not execute HTTP requests
        _device_code (:obj:`str`): auth0 code for a device
        _auth (:obj:`dict`): auth0 authorization type and token for a device for a user's account
    """

    def __init__(self, config=config, _dry_run=False):
        """
        Args:
            config (:obj:`object`, optional): package configuration
            _dry_run (:obj:`bool`, optional): if :obj:`True`, do not execute HTTP requests
        """
        self.config = config
        self._dry_run = _dry_run
        self._device_code = None
        self._auth = None

    def login(self):
        """ Login into BioSimulations using a browser """
        self._get_device_code()
        self._get_auth()

    def logout(self):
        """ Logout of BioSimulations

        Raises:
            :obj:`requests.exceptions.HTTPError`: if the user was not logged out
            :obj:`AssertionError`: if the user is not logged in or wasn't logged out
        """
        assert self._auth, "Must be logged into BioSimulations"

        if self._dry_run:
            patch = mock.patch('requests.post', return_value=mock.Mock(
                raise_for_status=lambda: None,
                content=b'',
                json=lambda: collections.defaultdict(str),
            ))
            patch.start()

        response = requests.post(self.config.auth0.endpoint + '/oauth/revoke', json={
            'client_id': self.config.auth0.client_id,
            'token': self._auth['token'],
        })
        response.raise_for_status()
        assert response.content == b''

        self._device_code = None
        self._auth = None

        if self._dry_run:
            patch.stop()

    def _get_device_code(self):
        """ Get a device code to authorize access to a BioSimulations account

        Raises:
            :obj:`requests.exceptions.HTTPError`: if a device code was not generated
        """
        if self._dry_run:
            patches = [
                mock.patch('requests.post', return_value=mock.Mock(
                    raise_for_status=lambda: None,
                    json=lambda: collections.defaultdict(str),
                )),
                mock.patch('webbrowser.open', return_value=None),
                mock.patch('click.confirm', return_value=None),
            ]
            for patch in patches:
                patch.start()

        response = requests.post(self.config.auth0.endpoint + '/oauth/device/code', json={
            'client_id': self.config.auth0.client_id,
            'scope': self.config.auth0.scope,
            'audience': self.config.auth0.audience,
        })
        response.raise_for_status()
        content = response.json()

        print("Please authorize access to your BioSimulations account:")
        print("  1. Open {} in your browser".format(content['verification_uri_complete']))
        print("  2. Click 'Confirm' to confirm the authorization code '{}'".format(content['user_code']))
        print("  3. Use your browser to log into your BioSimulations account")
        print("  4. You can now close your browser")
        webbrowser.open(content['verification_uri_complete'], new=2)
        click.confirm("  5. Enter 'Y' to continue", default=True, abort=True)

        self._device_code = content['device_code']

        if self._dry_run:
            for patch in patches:
                patch.stop()

    def _get_auth(self):
        """ Get the authorization header to access BioSimulations through a user's account

        Raises:
            :obj:`requests.exceptions.HTTPError`: if an authentication token was not generated
        """
        if self._dry_run:
            patch = mock.patch('requests.post', return_value=mock.Mock(
                raise_for_status=lambda: None,
                json=lambda: collections.defaultdict(str),
            ))
            patch.start()

        response = requests.post(self.config.auth0.endpoint + '/oauth/token', json={
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'device_code': self._device_code,
            'client_id': self.config.auth0.client_id,
        })
        response.raise_for_status()
        content = response.json()
        self._auth = {'type': content['token_type'], 'token': content['access_token']}

        if self._dry_run:
            patch.stop()

    def exec(self, method, route, data=None, response_type=ResponseType.json):
        """ Execute a route of the BioSimulations API

        Args:
            method (:obj:`str`): HTTP request method (e.g., 'get', 'post', 'put', 'patch', 'delete')
            route (:obj:`str`): route within the API (e.g., `/models/model-id` which gets
                information about model with id `model-id`)
            data (:obj:`object`): data for the route (e.g., `{name: 'model name', ...}` to
                use 'put' `/models/model-id` to change the name of the model with id `model-id`)
            response_type (:obj:`ResponseType`, optional): expected response type

        Raises:
            :obj:`requests.exceptions.HTTPError`: if the route was not successfully executed
        """
        if self._dry_run:
            route = 'post'
            patch = mock.patch('requests.post', return_value=mock.Mock(
                raise_for_status=lambda: None,
                json=lambda: None,
            ))
            patch.start()

        request_func = getattr(requests, method)

        opts = {}

        if data:
            opts['json'] = data

        if self._auth:
            opts['headers'] = {
                'Authorization': '{} {}'.format(self._auth['type'], self._auth['token']),
            }

        response = request_func(self.config.api.endpoint + route, **opts)
        response.raise_for_status()
        if response_type == ResponseType.json:
            content = response.json()
        elif response_type == ResponseType.bytes:
            content = response.content.decode()
        else:
            content = response.content

        if self._dry_run:
            patch.stop()

        return content
