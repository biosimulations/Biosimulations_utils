""" Package configuration

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import attrdict
import os

__all__ = [
    'auth0',
    'api',
    'combine_test_suite',
]

# Auth0
auth0 = attrdict.AttrDict({
    'endpoint': 'https://auth.biosimulations.org',
    'audience': 'api.biosimulations.org',
    'client_id': "3SN7foOQTrHQpdgjzjKwDsQjJTiYW9Js",
    'scope': None,
})

scope_methods = ['read', 'write']
scope_modules = ['Projects', 'Models', 'Simulations', 'Visualization', 'Files', 'Profile']
scopes = []
for method in scope_methods:
    for module in scope_modules:
        scopes.append('{}:{}'.format(method, module))
auth0['scope'] = ' '.join(scopes)

# REST API
api = attrdict.AttrDict({
    'endpoint': 'https://api.biosimulations.dev',
})

# test suite
combine_test_suite = attrdict.AttrDict({
    'dirname': os.getenv(
        'COMBINE_TEST_SUITE_DIR',
        os.path.expanduser(
            os.path.join(
                '~',
                'Documents',
                'Biosimulators_test_suite',
                'Biosimulators_test_suite',
            ),
        ),
    ),
})
