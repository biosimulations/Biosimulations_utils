""" Utilies for CI workflows for reviewing and committing simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-10-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import Action, ActionErrorHandling, IssueLabel
from ..simulator.testing import SimulatorValidator
import docker
import docker.errors
import json
import os
import requests
import simplejson.errors


class SimulatorAction(Action):
    """ Simulator continuous integration action

    Attributes:
        issue_number (:obj:`str`): number of GitHub issue which triggered the action
        docker_client (:obj:`docker.client.DockerClient`): Docker client
    """

    BIOSIMULATORS_AUTH_ENDPOINT = 'https://auth.biosimulations.org/oauth/token'
    BIOSIMULATORS_AUDIENCE = 'api.biosimulations.org'
    BIOSIMULATORS_VALIDATE_ENDPOINT = 'https://api.biosimulators.org/simulators/validate'
    BIOSIMULATORS_GET_ENDPOINT = 'https://api.biosimulators.org/simulators/{}'
    BIOSIMULATORS_POST_ENDPOINT = 'https://api.biosimulators.org/simulators'
    BIOSIMULATORS_PUT_ENDPOINT = 'https://api.biosimulators.org/simulators/{}/{}'
    IMAGE_REGISTRY = 'ghcr.io'
    IMAGE_REGISTRY_URL_PATTERN = 'ghcr.io/biosimulators/{}:{}'
    DEFAULT_SPECIFICATIONS_VERSION = '1.0.0'
    DEFAULT_IMAGE_VERSION = '1.0.0'

    def __init__(self):
        super(SimulatorAction, self).__init__()
        self.issue_number = self.get_issue_number()
        self.docker_client = docker.from_env()

    def get_submission(self, issue):
        """ Get the properties of the submission

        Args:
           issue (:obj:`dict`): properties of the GitHub issue for the submission

        Returns:
            :obj:`dict`: dictionary with `simulator`, `version`, and `specificationsUrl` keys
        """
        submission = self.get_data_in_issue(issue)

        simulator = submission.get('name', None) or None
        version = submission.get('version', None) or None
        specUrl = submission.get('specificationsUrl', None) or None

        # validate properties of submission
        errors = []
        if not simulator:
            errors.append('A simulator name must be provided.')
        if not version:
            errors.append('A simulator version must be provided.')
        if not specUrl:
            errors.append('A URL for the specifications of the simulator must be provided.')
        if errors:
            comment = ('Your simulator could not be verified. '
                       'Please edit the first block of this issue to re-initiate this validation.\n- ') + '\n- '.join(errors)
            self.add_error_comment_to_issue(self.issue_number, comment)

        return submission

    def get_specs(self, url):
        """ Get the specifications of the simulator
        Args:
            url (:obj:`str`): URL for the specifications of the simulator

        Returns:
            :obj:`dict`: specifications of the simulator
        """
        response = requests.get(url)

        # download specifications
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            self.add_error_comment_to_issue(
                self.issue_number,
                ('Your simulator could not be verified because we could not retrieve the specifications from {} ({}: {}). '
                    'Once the issue is fixed, edit the first block of this issue to re-initiate this validation.').format(
                    url, response.status_code, response.reason)
            )

        # check that specifications is valid JSON
        try:
            specs = response.json()
        except simplejson.errors.JSONDecodeError as error:
            self.add_error_comment_to_issue(
                self.issue_number,
                ('Your simulator code not be verified because the specifications are not valid JSON:\n\n  {}\n\n'
                    'Once the issue is fixed, edit the first block of this issue to re-initiate this validation.').format(str(error)))

        # validate specifications
        response = requests.post(self.BIOSIMULATORS_VALIDATE_ENDPOINT, json=specs)
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            self.add_error_comment_to_issue(
                self.issue_number,
                ('Your specifications are not valid.\n\n{}\n\n'
                    'Once the issue is fixed, edit the first block of this issue to re-initiate this validation.').format(
                    response.reason.rstrip().replace('\n', '\n  ')))

        # return specifications
        return specs

    @classmethod
    def get_image_version(cls, simulator):
        """ Get the BioSimulators version of a simulator

        Args:
            simulator (:obj:`dict`): simulator specifications

        Returns:
            :obj:`str`: BioSimulators version of the simulator
        """
        return '{}-{}'.format(
            simulator.get('biosimulators', {}).get('specificationsVersion', cls.DEFAULT_SPECIFICATIONS_VERSION),
            simulator.get('biosimulators', {}).get('imageVersion', cls.DEFAULT_IMAGE_VERSION))

    def pull_docker_image(self, url):
        """ Pull Docker image

        Args:
            url (:obj:`str`): URL for Docker image

        Returns:
            :obj:`docker.models.images.Image`: Docker image
        """
        # login to Docker Hub to avoid access limits for anonymous users
        self.docker_client.login(
            username=os.getenv('DOCKER_HUB_USERNAME'),
            password=os.getenv('DOCKER_HUB_TOKEN'),
        )

        # pull image
        try:
            return self.docker_client.images.pull(url)
        except docker.errors.NotFound:
            self.add_error_comment_to_issue(
                issue_number,
                (
                    'Your container could not be verified because no image is at the URL {}. '
                    'After correcting the specifications, please edit the first block of this issue to re-initiate this validation.'
                ).format(url))
        except Exception as error:
            self.add_error_comment_to_issue(
                issue_number,
                (
                    'Your container could not be verified: {}. '
                    'After correcting the specifications, please edit the first block of this issue to re-initiate this validation.'
                ).format(str(error)))

    def tag_and_push_image(self, image, tag):
        """ Tag and push Docker image

        Args:
            image (:obj:`docker.models.images.Image`): Docker image
            tag (:obj:`str`): tag
        """
        assert image.tag(tag)
        response = self.docker_client.images.push(tag)
        response = json.loads(response.rstrip().split('\n')[-1])
        if 'error' in response:
            raise Exception('Unable to push image to {}'.format(tag))

    def get_simulator_version_specs(self, id):
        """ Get the versions of a simulator already in the BioSimulators registry

        Args:
            id (:obj:`str`): simulator id

        Returns:
            :obj:`list` of :obj:`dict`: specifications of the registered versions of the simulator
        """
        response = requests.get(self.BIOSIMULATORS_GET_ENDPOINT.format(id))
        try:
            response.raise_for_status()
            version_specs = response.json()
        except requests.exceptions.HTTPError:
            if response.status_code != 404:
                raise
            version_specs = []
        return version_specs


class ValidateSimulatorAction(SimulatorAction):
    """ Action to validate a containerized simulator """

    @ActionErrorHandling.catch_errors(Action.get_issue_number())
    def run(self):
        """ Validate a submission of simulator. Called by `Validate Simulator` CI action. """

        # retrieve issue
        issue_number = self.issue_number
        issue = self.get_issue(issue_number)
        submitter = issue['user']['login']

        # report message that review is starting
        self.add_comment_to_issue(issue_number,
                                  ('Thank you @{} for your submission to the BioSimulators registry of containerized simulation tools! '
                                   '[Action {}]({}) is reviewing your submission. We will discuss any issues with your submission here.'
                                   ).format(submitter, self.gh_action_run_id, self.gh_action_run_url))

        # reset labels
        labels = self.get_labels_for_issue(issue_number)
        if IssueLabel.validated in labels:
            self.remove_label_from_issue(issue_number, IssueLabel.validated)
        if IssueLabel.invalid in labels:
            self.remove_label_from_issue(issue_number, IssueLabel.invalid)
        if IssueLabel.approved in labels:
            self.remove_label_from_issue(issue_number, IssueLabel.approved)
        if IssueLabel.action_error in labels:
            self.remove_label_from_issue(issue_number, IssueLabel.action_error)

        # parse submision
        submisssion = self.get_submission(issue)
        specUrl = submisssion['specificationsUrl']

        # validate specifications
        specs = self.get_specs(specUrl)
        self.add_comment_to_issue(issue_number, 'The specifications of your simulator is valid!')

        # validate that container (Docker image) exists
        image_url = specs['image']
        self.pull_docker_image(image_url)

        # TODO: validate container
        # validator = SimulatorValidator()
        # validCases, testExceptions, skippedCases = validator.run(image_url, specs)

        # self.add_comment_to_issue(issue_number, 'Your container passed {} test cases.'.format(len(validCases)))

        # error_msgs = []

        # if not validCases:
        #     error_msgs.append(('No test cases are applicable to your container. '
        #                        'Please use this issue to share appropriate test COMBINE/OMEX files for the BioSimulators test suite. '
        #                        'The BioSimulators Team will add these files to the test suite and then re-review your simulator.'
        #                        ))

        # if testExceptions:
        #     msgs = []
        #     for exception in testExceptions:
        #         msgs.append('- {}\n  {}\n\n'.format(exception.test_case, str(exception.exception)))

        #     error_msgs.append((
        #         'Your container did not pass {} test cases.\n\n{}'
        #         'After correcting the container, please edit the first block of this issue to re-initiate this validation.'
        #     ).format(len(testExceptions), ''.join(msgs)))

        # if error_msgs:
        #     self.add_error_comment_to_issue(issue_number, '\n\n'.join(error_msgs))

        # self.add_comment_to_issue(issue_number, 'Your containerized simulator is valid!')

        # label issue as validated
        self.add_labels_to_issue(self.issue, [IssueLabel.validated])

        # label the issue as approved if the issue is a revision of an existing simulator or a new version of an existing simulator
        existing_version_specs = self.get_simulator_version_specs(specs['id'])
        if existing_version_specs:
            self.add_labels_to_issue(self.issue, [IssueLabel.approved])

        # post success message
        self.add_comment_to_issue(
            issue_number,
            'A member of the BioSimulators team will review your submission before final committment to the registry.')


class CommitSimulatorAction(SimulatorAction):
    """ Action to commit a containerized simulator to the BioSimulators registry """

    @ActionErrorHandling.catch_errors(Action.get_issue_number())
    def run(self):
        """ Commit a simulator (id and version) to the BioSimulators registry. Called by the `Commit Simulator` CI action """

        issue_number = self.issue_number
        issue = self.get_issue(issue_number)
        submisssion = self.get_submission(issue)
        specUrl = submisssion['specificationsUrl']
        specs = self.get_specs(specUrl)

        self.add_comment_to_issue(issue_number,
                                  '[Action {}]({}) is committing your submission to the BioSimulators registry.'.format(
                                      self.gh_action_run_id, self.gh_action_run_url))

        # get other versions of simulator
        existing_version_specs = self.get_simulator_version_specs(specs['id'])

        # pull image
        original_image_url = specs['image']
        image = self.pull_docker_image(original_image_url)

        # push image to Docker container registry
        self.docker_client.login(
            registry=self.IMAGE_REGISTRY,
            username=os.getenv('GH_ISSUES_USER'),
            password=os.getenv('GH_ISSUES_ACCESS_TOKEN'),
        )

        copy_image_url = self.IMAGE_REGISTRY_URL_PATTERN.format(
            specs['id'],
            specs['version'] + '-' + self.get_image_version(specs))
        self.tag_and_push_image(image, copy_image_url)
        specs['image'] = copy_image_url

        is_latest_of_version = True
        is_latest = True
        for version_spec in existing_version_specs:
            if version_spec['version'] == specs['version'] and self.get_image_version(version_spec) > self.get_image_version(specs):
                is_latest_of_version = False
            if version_spec['version'] > specs['version'] or self.get_image_version(version_spec) > self.get_image_version(specs):
                is_latest = False

        if is_latest_of_version:
            latest_of_version_copy_image_url = self.IMAGE_REGISTRY_URL_PATTERN.format(
                specs['id'],
                specs['version'])
            self.tag_and_push_image(image, latest_of_version_copy_image_url)

        if is_latest:
            latest_copy_image_url = self.IMAGE_REGISTRY_URL_PATTERN.format(
                specs['id'],
                'latest')
            self.tag_and_push_image(image, latest_copy_image_url)

        # determine if container needs to be added or updated
        existing_versions = [version_spec['version'] for version_spec in existing_version_specs]
        update_simulator = specs['version'] in existing_versions

        # commit submission to BioSimulators database
        api_id = os.getenv('BIOSIMULATORS_API_CLIENT_ID')
        api_secret = os.getenv('BIOSIMULATORS_API_CLIENT_SECRET')

        response = requests.post(self.BIOSIMULATORS_AUTH_ENDPOINT, json={
            'client_id': api_id,
            'client_secret': api_secret,
            'audience': self.BIOSIMULATORS_AUDIENCE,
            "grant_type": "client_credentials",
        })
        response.raise_for_status()
        response_data = response.json()
        auth_headers = {'Authorization': response_data['token_type'] + ' ' + response_data['access_token']}

        if update_simulator:
            endpoint = self.BIOSIMULATORS_PUT_ENDPOINT.format(specs['id'], specs['version'])
            requests_method = requests.put
        else:
            endpoint = self.BIOSIMULATORS_POST_ENDPOINT
            requests_method = requests.post
        response = requests_method(endpoint, headers=auth_headers, json=specs)
        response.raise_for_status()

        # post success message
        self.add_comment_to_issue(
            issue_number,
            ''.join([
                'Your submission was committed to the BioSimulators registry. Thank you!\n',
                '\n',
                'Future submissions of subsequent versions of {} to the BioSimulators registry '.format(specs['id']),
                'will be automatically validated. These submissions will not require manual review by the BioSimulators Team.',
            ])
        )

        # close issue
        self.close_issue(issue_number)
