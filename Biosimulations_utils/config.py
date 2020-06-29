""" Package configuration

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import attrdict

__all__ = [
    'auth0',
    'api',
]

auth0 = attrdict.AttrDict({
    'endpoint': 'https://crbm.auth0.com',
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

api = attrdict.AttrDict({
    'endpoint': 'https://api.biosimulations.dev',
})
