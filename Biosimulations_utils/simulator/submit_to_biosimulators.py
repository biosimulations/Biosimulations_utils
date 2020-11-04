""" Methods for submitting simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-10-30
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import requests

GH_ISSUE_ENDPOINT = 'https://api.github.com/repos/biosimulators/Biosimulators/issues'


def submit_simulator_to_biosimulators(name, version, specUrl, gh_username, gh_access_token):
    """ Submit a version of a simulation tool for review for inclusion in the BioSimulators registry. 
    This will create a GitHub issue which the BioSimulators Team will use to review your submission.

    This method requires a GitHub access and personal access token. This access token must have the `public_repo` scope.
    Instructions for creating an access token are available in the
    `GitHub documentation <https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token`>_.

    Args:
        name (:obj:`str`): name (e.g., `tellurium` or `VCell`)
        version (:obj:`str`): version (e.g., `2.1.6`)
        specUrl (:obj:`str`): URL to the specifications of the version of the simulator 
            (e.g., `https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/2.1.6/biosimulators.json`)
        gh_username (:obj:`str`): GitHub username (e.g., `jonrkarr`)
        gh_access_token (:obj:`str`): GitHub personal access token.

    Raises:
        :obj:`requests.exceptions.HTTPError`: if the simulator is not successfully submitted for review
    """

    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }

    data = {
        "labels": ["Submit simulator", "Validated"],
        "title": "Submit {} {}".format(name, version),
        "body": "\n".join([
            "---",
            "name: {}".format(name),
            "version: {}".format(version),
            "specificationsUrl: {}".format(specUrl),
            "",
            "---",
        ]),
    }

    response = requests.post(GH_ISSUE_ENDPOINT,
                             headers=headers,
                             auth=(gh_username, gh_access_token),
                             json=data)
    response.raise_for_status()
