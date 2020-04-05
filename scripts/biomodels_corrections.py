""" Manual corrections to BioModels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-05
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.model.sbml import viz_model
import json
import os
import shutil

cache_dir = os.path.expanduser('~/.cache/Biosimulations_format_utils')
models_filename = os.path.join(cache_dir, 'biomodels.models.json')
sims_filename = os.path.join(cache_dir, 'biomodels.simulations.json')
fix_images = ['BIOMD0000000075', 'BIOMD0000000081', 'BIOMD0000000353']

# models
for fix_image in fix_images:
    viz_model(
        os.path.join('scripts', fix_image + '-corrected-for-image.xml'),
        os.path.join(cache_dir, fix_image + '.png'))

with open(models_filename, 'r') as file:
    models = json.load(file)

for model in models:
    if model['id'] in fix_images:
        model['image'] = {
            'name': model['file']['name'].replace('.xml', '.png'),
            'type': 'image/png',
            'size': os.path.getsize(os.path.join(cache_dir, model['id'] + '.png')),
        }

with open(models_filename, 'w') as file:
    json.dump(models, file)

# simulations
with open(sims_filename, 'r') as file:
    sims = json.load(file)

for sim in sims:
    if sim['model']['id'] in fix_images:
        sim['image'] = {
            'name': sim['id'] + '.png',
            'type': 'image/png',
            'size': os.path.getsize(os.path.join(cache_dir, sim['model']['id'] + '.png')),
        }
        shutil.copyfile(
            os.path.join(cache_dir, sim['model']['id'] + '.png'),
            os.path.join(cache_dir, sim['id'] + '.png'))

with open(sims_filename, 'w') as file:
    json.dump(sims, file)
