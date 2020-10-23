""" Utilies for CI workflows for reviewing and committing simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-10-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import Action, ActionErrorHandling
import requests
import simplejson.errors


class SimulatorAction(Action):
    # BIOSIMULATORS_VALIDATE_ENDPOINT = 'https://api.biosimulators.org/simulators/validate'
    BIOSIMULATORS_POST_ENDPOINT = 'https://api.biosimulators.org/simulators'

    def __init__(self):
        super(SimulatorAction, self).__init__()
        self.issue_number = self.get_issue_number()

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
        # TODO: set validation endpoint
        # response = requests.get(self.BIOSIMULATORS_VALIDATE_ENDPOINT, data=specs)
        # try:
        #    response.raise_for_status()
        # except requests.RequestException as error:
        #    self.add_error_comment_to_issue(
        #        self.issue_number,
        #        ('Your specifications are not valid.\n\n{}\n\n'
        #            'Once the issue is fixed, edit the first block of this issue to re-initiate this validation.').format(
        #            response.reason.rstrip().replace('\n', '\n  ')))

        # return specifications
        return specs


class ValidateSimulatorAction(SimulatorAction):
    @ActionErrorHandling.catch_errors(Action.get_issue_number())
    def run(self):
        """ Validate a submission of simulator. Called by `Validate Simulator` CI action. """

        # retrieve issue
        issue_number = self.issue_number
        issue = self.get_issue(issue_number)
        submitter = issue['user']['login']
        self.add_comment_to_issue(issue_number,
                                  ('Thank you @{} for your submission to the BioSimulators registry of containerized simulation tools! '
                                   '[Action {}]({}) is reviewing your submission. We will discuss any issues with your submission here.'
                                   ).format(submitter, self.gh_action_run_id, self.gh_action_run_url))

        # parse submision
        submisssion = self.get_submission(issue)
        specUrl = submisssion['specificationsUrl']

        # validate specifications
        specs = self.get_specs(specUrl)
        self.add_comment_to_issue(issue_number, 'The specifications of your simulator is valid!')

        # validate that container (Docker image) exists
        import docker
        import docker.errors
        image_url = specs['image']
        docker_client = docker.from_env()
        try:
            docker_client.images.pull(image_url)
        except docker.errors.NotFound:
            self.add_error_comment_to_issue(
                issue_number,
                (
                    'Your container could not be verified because no image is at the URL {}. '
                    'After correcting the specifications, please edit the first block of this issue to re-initiate this validation.'
                ).format(image_url))
        except Exception as error:
            self.add_error_comment_to_issue(
                issue_number,
                (
                    'Your container could not be verified: {}. '
                    'After correcting the specifications, please edit the first block of this issue to re-initiate this validation.'
                ).format(str(error)))

        # validate container
        from ..simulator.testing import SimulatorValidator
        validator = SimulatorValidator()
        validCases, testExceptions, skippedCases = validator.run(image_url, specs)

        self.add_comment_to_issue(issue_number, 'Your container passed {} test cases.'.format(len(validCases)))

        error_msgs = []

        raise ValueError('here')
        # if not validCases:
        #    error_msgs.append(('No test cases are applicable to your container. '
        #                       'Please use this issue to share appropriate test COMBINE/OMEX files for the BioSimulators test suite. '
        #                       'The BioSimulators Team will add these files to the test suite and then re-review your simulator.'
        #                       ))

        if testExceptions:
            msgs = []
            for exception in testExceptions:
                msgs.append('- {}\n  {}\n\n'.format(exception.test_case, str(exception.exception)))

            error_msgs.append((
                'Your container did not pass {} test cases.\n\n{}'
                'After correcting the container, please edit the first block of this issue to re-initiate this validation.'
            ).format(len(testExceptions), ''.join(msgs)))

        if error_msgs:
            self.add_error_comment_to_issue(issue_number, '\n\n'.join(error_msgs))

        self.add_comment_to_issue(issue_number, 'Your containerized simulator is valid!')

        # label issue as `validated`
        self.add_labels_to_issue(self.issue, ['Validated'])
        if 'Action error' in self.get_labels_for_issue(issue_number):
            self.remove_label_from_issue(issue_number, 'Action error')

        # post success message
        self.add_comment_to_issue(
            issue_number,
            'A member of the BioSimulators team will review your submission before final committment to the registry.')


class CommitSimulatorAction(SimulatorAction):
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

        # commit submission to BioSimulators database
        # TODO: incorporate authentication
        # requests.post(self.BIOSIMULATORS_POST_ENDPOINT, data=specs)

        # post success message
        self.add_comment_to_issue(
            issue_number,
            'Your submission was committed to the BioSimulators registry. Thank you!')

        # close issue
        self.close_issue(issue_number)
