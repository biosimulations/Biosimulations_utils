""" Import models from BioModels into BioSimulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-23
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Identifier, JournalReference, License, Person, RemoteFile
from ..model import ModelFormat, read_model
from ..model.core import ModelIoError
from ..model.data_model import Model  # noqa: F401
from ..model.sbml import viz_model
from ..sim import SimFormat, read_sim
from ..sim.core import SimIoWarning
from ..sim.data_model import Simulation
import copy
import json
import libsbml
import math
import os
import re
import requests
import requests.adapters
import requests_cache
import shutil
import warnings
import xml.etree.ElementTree


__all__ = ['BioModelsImporter']


class BioModelsImporter(object):
    """ Import models from BioModels

    Attributes:
        _max_models (:obj:`int`): maximum number of models to download from BioModels
        _cache_dir (:obj:`str`): directory to cache models from BioModels
        _requests_session (:obj:`requests_cache.core.CachedSession`): requests cached session
    """
    BIOMODELS_ENDPOINT = 'https://www.ebi.ac.uk/biomodels'
    PUBMED_ENDPOINT = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    BIOSIMULATIONS_ENDPOINT = 'https://api.biosimulations.dev'
    NUM_MODELS_PER_BATCH = 100
    MAX_RETRIES = 5

    def __init__(self, _max_models=float('inf'), _cache_dir=None):
        self._max_models = _max_models
        self._cache_dir = _cache_dir
        self.init_requests_cache()

    def init_requests_cache(self):
        if self._cache_dir is None:
            self._cache_dir = os.path.expanduser('~/.cache/Biosimulations_format_utils')
        if not os.path.isdir(self._cache_dir):
            os.makedirs(self._cache_dir)

        self._requests_session = requests_cache.core.CachedSession(
            os.path.join(self._cache_dir, 'biomodels'), backend='sqlite', expire_after=None)
        self._requests_session.mount('https://',
                                     requests.adapters.HTTPAdapter(max_retries=self.MAX_RETRIES))

    def run(self):
        """ Retrieve models from BioModels and submit to BioSimulations

        Returns:
            :obj:`list` of :obj:`Model`: models
            :obj:`list` of :obj:`Simulation`: simulations
            :obj:`dict`: statistics about the models
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('ignore')
            warnings.simplefilter('always', SimIoWarning)
            models, sims = self.get_models()
        if caught_warnings:
            warnings.warn('Unable to import all simlations:\n  ' + '\n  '.join(
                str(w.message) for w in caught_warnings), UserWarning)
        self.submit_models(models)
        stats = self.get_stats(models, sims)
        self.write_data(models, sims, stats)
        return (models, sims, stats)

    def get_models(self):
        """ Get models from BioModels

        Returns:
            :obj:`list` of :obj:`Model`: list of metadata about each model
            :obj:`list` of :obj:`Simulation`: list of metadata about each simulation
        """
        models = []
        sims = []
        unimportable_models = []
        unvisualizable_models = []
        num_models = min(self._max_models, self.get_num_models())
        print('Importing {} models'.format(num_models))
        for i_batch in range(int(math.ceil(num_models / self.NUM_MODELS_PER_BATCH))):
            results = self.get_model_batch(num_results=self.NUM_MODELS_PER_BATCH, i_batch=i_batch)
            for i_model, model_result in enumerate(results['models']):
                print('  {}. {}: {}'.format(i_batch * self.NUM_MODELS_PER_BATCH + i_model + 1, model_result['id'], model_result['name']))
                try:
                    model, model_sims = self.get_model(model_result['id'])
                    models.append(model)
                    sims.extend(model_sims)
                except ModelIoError:
                    unimportable_models.append(model_result['id'])

                try:
                    model.image = self.viz_model(model)
                    for sim in model_sims:
                        sim.image = RemoteFile(
                            name=sim.id + '.png',
                            type='image/png',
                            size=model.image.size)
                        shutil.copyfile(os.path.join(self._cache_dir, model.id + '.png'), os.path.join(self._cache_dir, sim.image.name))

                except ModelIoError:
                    unvisualizable_models.append(model_result['id'])

                if len(models) == self._max_models:
                    break

        if unimportable_models:
            warnings.warn('Unable import the following models:\n  {}'.format('\n  '.join(sorted(unimportable_models))), UserWarning)
        if unvisualizable_models:
            warnings.warn('Unable visualize the following models:\n  {}'.format('\n  '.join(sorted(unvisualizable_models))), UserWarning)

        return (models, sims)

    def get_num_models(self):
        """ Get the number of models to import

        Returns:
            :obj:`int`: number of models to import
        """
        return self.get_model_batch()['matches']

    def get_model_batch(self, num_results=10, i_batch=0):
        """ Retrieve a batch of models

        Args:
            num_results (:obj:`int`, optional): number of results to retrieve
            i_batch (:obj:`int`, optional): index of batch to retrieve

        Returns:
            :obj:`dict`: batch of models
        """
        response = self._requests_session.get(
            self.BIOMODELS_ENDPOINT + '/search',
            params={
                'query': 'modelformat:"SBML" AND curationstatus:"Manually curated"',
                'sort': 'id-asc',
                'numResults': min(self._max_models, num_results),
                'offset': i_batch * self.NUM_MODELS_PER_BATCH,
            },
            headers={
                'accept': 'application/json',
            })
        response.raise_for_status()
        return response.json()

    def get_model(self, id):
        """ Get a model

        Args:
            id (:obj:`str`): model id

        Returns:
            :obj:`Model`: information about model
            :obj:`list` of :obj:`Simulation`: information about simulations
        """
        metadata = self.get_model_metadata(id)
        files_metadata = self.get_model_files_metadata(id)

        # get information about model
        if 'publication' in metadata:
            doi = None
            authors = []
            authors_str = []
            for author in metadata['publication'].get('authors', []):
                last_name, _, first_name = author['name'].partition(' ')

                authors.append(Person(first_name=first_name, last_name=last_name))

                author_str = []
                if first_name:
                    author_str.append(first_name)
                if last_name:
                    author_str.append(last_name)

                if author_str:
                    authors_str.append(' '.join(author_str))

            match = re.match(r'^https?://identifiers\.org/pubmed/(\d+)$', metadata['publication']['link'])

            if match:
                pubmed_id = match.group(1)
                response = self._requests_session.get(self.PUBMED_ENDPOINT, params={
                    'db': 'pubmed',
                    'id': pubmed_id,
                    'retmode': 'xml'
                })
                response.raise_for_status()
                pub_xml = xml.etree.ElementTree.fromstring(response.content).find('PubmedArticle')

                doi = None
                if pub_xml is not None:
                    pub_ids_xml = pub_xml.find('PubmedData').find('ArticleIdList').findall('ArticleId')
                    for pub_id_xml in pub_ids_xml:
                        if pub_id_xml.get('IdType') == 'doi':
                            doi = pub_id_xml.text
                            break

                authors = []
                authors_str = ''
                if pub_xml is not None:
                    authors_str = []
                    authors_xml = pub_xml.find('MedlineCitation').find('Article').find('AuthorList').findall('Author')
                    for author_xml in authors_xml:
                        last_name_xml = author_xml.find('LastName')
                        if last_name_xml is not None:
                            last_name = last_name_xml.text or None
                        else:
                            last_name = None

                        fore_name_xml = author_xml.find('ForeName')
                        if fore_name_xml is not None:
                            first_name, _, middle_name = fore_name_xml.text.partition(' ')
                            first_name = first_name or None
                            middle_name = middle_name or None
                        else:
                            first_name = None
                            middle_name = None

                        authors.append(Person(
                            last_name=last_name,
                            first_name=first_name,
                            middle_name=middle_name,
                        ))

                        author_str = []
                        if first_name:
                            author_str.append(first_name)
                        if middle_name:
                            author_str.append(middle_name)
                        if last_name:
                            author_str.append(last_name)

                        if author_str:
                            authors_str.append(' '.join(author_str))

            if len(authors_str) == 0:
                authors_str = ''
            elif len(authors_str) == 1:
                authors_str = authors_str[-1]
            else:
                authors_str = ', '.join(authors_str[0:-1]) + ' & ' + authors_str[-1]

            references = [
                JournalReference(
                    authors=authors_str,
                    title=metadata['publication']['title'],
                    journal=metadata['publication']['journal'],
                    volume=metadata['publication'].get('volume', None),
                    num=metadata['publication'].get('issue', None),
                    pages=metadata['publication'].get('pages', None),
                    year=metadata['publication'].get('year', None),
                    doi=doi,
                ),
            ]
        else:
            authors = []
            references = []

        model_filename = files_metadata['main'][0]['name']
        local_path = os.path.join(self._cache_dir, id + '.xml')
        with open(local_path, 'wb') as file:
            file.write(self.get_model_file(id, model_filename))

        model = read_model(local_path, format=ModelFormat.sbml)
        model.id = id
        model.name = metadata['name']
        model.file = RemoteFile(
            name=model_filename,
            type='application/sbml+xml',
            size=os.path.getsize(local_path),
        )
        model.description = metadata.get('description', None)
        if model.description:
            try:
                description_xml = xml.dom.minidom.parseString(model.description)
                for div_xml in description_xml.getElementsByTagNameNS('http://www.w3.org/1999/xhtml', 'div'):
                    if div_xml.getAttribute('class') == 'dc:description':
                        div_xml.removeAttribute('class')
                        model.description = div_xml.toxml()
            except Exception:
                pass
        model.identifiers = [Identifier(namespace='biomodels.db', id=metadata['publicationId'])]
        model.references = references
        model.authors = authors
        model.license = License.cc0

        # get information about simulation(s)
        sims = []
        num_sim_files = 0
        for file_metadata in files_metadata['additional']:
            if file_metadata['name'].endswith('.sedml'):
                num_sim_files += 1
                local_path = os.path.join(self._cache_dir, '{}-{}.sedml'.format(model.id, num_sim_files))
                with open(local_path, 'wb') as file:
                    file.write(self.get_model_file(id, file_metadata['name']))

                model_sims = read_sim(local_path, ModelFormat.sbml, SimFormat.sedml)

                model_files = set([sim.model.file.name for sim in model_sims]).difference(set(['model']))
                assert len(model_files) <= 1, 'Each simulation must use the same model'

                for sim in model_sims:
                    sim.id = '{}-sim-{}'.format(model.id, len(sims) + 1)
                    sim.name = file_metadata['name'][0:-6]
                    sim.description = file_metadata['description']
                    sim.identifiers = [Identifier(namespace='biomodels.db', id=metadata['publicationId'])]
                    sim.references = copy.deepcopy(model.references)
                    sim.authors = copy.deepcopy(model.authors)
                    sim.license = License.cc0
                    sim.model.id = model.id
                    sim.model.name = model.name
                    sim.model.file = None
                sims.extend(model_sims)
        if len(sims) == 1:
            sims[0].id = '{}-sim'.format(model.id)
            os.rename(
                os.path.join(self._cache_dir, '{}-{}.sedml'.format(model.id, 1)),
                os.path.join(self._cache_dir, '{}.sedml'.format(model.id)))

        return (model, sims)

    def get_model_metadata(self, id):
        """ Get metadata about a model

        Args:
            id (:obj:`str`): model id

        Returns:
            :obj:`dict`: metadata about the files of a model
        """
        response = self._requests_session.get(
            self.BIOMODELS_ENDPOINT + '/' + id,
            headers={
                'accept': 'application/json',
            })
        response.raise_for_status()
        return response.json()

    def get_model_files_metadata(self, id):
        """ Get metadata about the files of a model

        Args:
            id (:obj:`str`): model id

        Returns:
            :obj:`dict`: metadata about the files of a model
        """
        response = self._requests_session.get(
            self.BIOMODELS_ENDPOINT + '/model/files/' + id,
            headers={
                'accept': 'application/json',
            })
        response.raise_for_status()
        return response.json()

    def get_model_file(self, id, filename):
        response = self._requests_session.get(
            self.BIOMODELS_ENDPOINT + '/model/download/' + id,
            params={
                'filename': filename,
            },
            headers={
                'accept': 'application/json',
            })
        response.raise_for_status()
        return response.content

    def viz_model(self, model):
        """ Generate a visualization of a model

        Args:
            model (:obj:`Model`): model

        Returns:
            :obj:`RemoteFile`: image
        """
        model_basename = model.id + '.xml'
        img_basename = model.id + '.png'

        model_path = os.path.join(self._cache_dir, model_basename)
        img_path = os.path.join(self._cache_dir, img_basename)

        img = viz_model(model_path, img_path, requests_session=self._requests_session)
        assert model.file.name.endswith('.xml')
        img.name = model.file.name[0:-4] + '.png'
        return img

    def submit_models(self, models):
        """ Post models to BioSimulations

        Args:
            models (:obj:`list` of :obj:`Model`):
        """
        for model in models:
            # Todo: submit models to BioSimulations
            # requests.post(self.BIOSIMULATIONS_ENDPOINT)
            pass

    def write_data(self, models, sims, stats):
        """ Save models and simulations to JSON files

        Args:
            models (:obj:`list` of :obj:`Model`): models
            sims (:obj:`list` of :obj:`Simulation`): simulations
            stats (:obj:`dict`): statistics of the models
        """
        filename = os.path.join(self._cache_dir, 'biomodels.models.json')
        with open(filename, 'w') as file:
            json.dump([model.to_json() for model in models], file)

        filename = os.path.join(self._cache_dir, 'biomodels.simulations.json')
        with open(filename, 'w') as file:
            json.dump([sim.to_json() for sim in sims], file)

        filename = os.path.join(self._cache_dir, 'biomodels.stats.json')
        with open(filename, 'w') as file:
            json.dump(stats, file)

    def read_data(self):
        """ Read models and simulations from JSON files

        Returns:
            :obj:`list` of :obj:`Model`: models
            :obj:`list` of :obj:`Simulation`: simulations
            :obj:`dict`: stats about the models
        """
        filename = os.path.join(self._cache_dir, 'biomodels.models.json')
        with open(filename, 'r') as file:
            models = [Model.from_json(model) for model in json.load(file)]

        filename = os.path.join(self._cache_dir, 'biomodels.simulations.json')
        with open(filename, 'r') as file:
            sims = [Simulation.from_json(sims) for sims in json.load(file)]

        filename = os.path.join(self._cache_dir, 'biomodels.stats.json')
        with open(filename, 'r') as file:
            stats = json.load(file)

        return (models, sims, stats)

    def get_stats(self, models, sims):
        """ Calculate statistics about the imported models

        Args:
            models (:obj:`list` of :obj:`Model`): models
            sims (:obj:`list` of :obj:`Simulation`): simulations

        Returns:
            :obj:`dict`: statistics about the imported models
        """
        stats = {
            'models': {
                'total': len(models),
                'frameworks': {},
                'layouts': 0,
                'taxa': {},
                'simulated': len(set(sim.model.id for sim in sims)),
            },
            'sims': {
                'total': len(sims),
                'time course': 0,
                'one step': 0,
                'steady-state': 0,
            }
        }

        for model in models:
            framework = model.framework.name
            if framework not in stats['models']['frameworks']:
                stats['models']['frameworks'][framework] = 0
            stats['models']['frameworks'][framework] += 1

            doc = libsbml.readSBMLFromFile(os.path.join(self._cache_dir, model.id + '.xml'))
            plugin = doc.getModel().getPlugin('layouts')
            if plugin and plugin.getNumLayouts():
                stats['models']['layouts'] += 1

            if model.taxon:
                if model.taxon.name not in stats['models']['taxa']:
                    stats['models']['taxa'][model.taxon.name] = 0
                stats['models']['taxa'][model.taxon.name] += 1

        for sim in sims:
            if sim.num_time_points is None:
                stats['sims']['steady-state'] += 1
            elif sim.num_time_points == 2:
                stats['sims']['one step'] += 1
            else:
                stats['sims']['time course'] += 1

        return stats
