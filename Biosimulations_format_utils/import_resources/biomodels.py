""" Import models from BioModels into BioSimulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-23
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..api_client import ApiClient
from ..data_model import Identifier, JournalReference, License, Person, RemoteFile
from ..model import read_model
from ..model.core import ModelIoError
from ..model.data_model import ModelFormat, Model  # noqa: F401
from ..model.sbml import viz_model
from ..simulation import read_sim
from ..simulation.core import SimIoError, SimIoWarning
from ..simulation.data_model import SimFormat, Simulation
from ..visualization.data_model import Visualization
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
        _dry_run (:obj:`bool`): if :obj:`True`, do not post models to BioModels
        _requests_session (:obj:`requests_cache.core.CachedSession`): requests cached session
    """
    BIOMODELS_ENDPOINT = 'https://www.ebi.ac.uk/biomodels'
    PUBMED_ENDPOINT = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    BIOSIMULATIONS_ENDPOINT = 'https://api.biosimulations.dev'
    NUM_MODELS_PER_BATCH = 100
    MAX_RETRIES = 5

    def __init__(self, _max_models=float('inf'), _cache_dir=None, _dry_run=False):
        """
        Args:
            _max_models (:obj:`int`, optional): maximum number of models to download from BioModels
            _cache_dir (:obj:`str`, optional): directory to cache models from BioModels
            _dry_run (:obj:`bool`, optional): if :obj:`True`, do not post models to BioModels
        """
        self._max_models = _max_models
        self._cache_dir = _cache_dir
        self._dry_run = _dry_run
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
            :obj:`list` of :obj:`Visualization`: visualizations
            :obj:`dict`: statistics about the models
        """
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('ignore')
            warnings.simplefilter('always', SimIoWarning)
            warnings.simplefilter('always', BiomodelsIoWarning)
            models, sims, vizs = self.get_models()
        if caught_warnings:
            for caught_warning in caught_warnings:
                if caught_warning.category == BiomodelsIoWarning:
                    warnings.warn(str(caught_warning.message), UserWarning)

            warnings.warn('Unable to import all simulations:\n  ' + '\n  '.join(
                str(w.message) for w in caught_warnings if w.category == SimIoWarning), UserWarning)
        self.submit_models(models, sims, vizs)
        stats = self.get_stats(models, sims, vizs)
        self.write_data(models, sims, vizs, stats)
        return (models, sims, vizs, stats)

    def get_models(self):
        """ Get models from BioModels

        Returns:
            :obj:`list` of :obj:`Model`: list of metadata about each model
            :obj:`list` of :obj:`Simulation`: list of metadata about each simulation
            :obj:`list` of :obj:`Visualization`: list of metadata about each visualization
        """
        models = []
        sims = []
        vizs = []
        unimportable_models = []
        unimportable_sims = []
        unvisualizable_models = []
        num_models = min(self._max_models, self.get_num_models())
        print('Importing {} models'.format(num_models))
        for i_batch in range(int(math.ceil(num_models / self.NUM_MODELS_PER_BATCH))):
            results = self.get_model_batch(num_results=self.NUM_MODELS_PER_BATCH, i_batch=i_batch)
            for i_model, model_result in enumerate(results['models']):
                print('  {}. {}: {}'.format(i_batch * self.NUM_MODELS_PER_BATCH + i_model + 1, model_result['id'], model_result['name']))
                try:
                    model, model_sims, model_vizs = self.get_model(model_result['id'])
                    models.append(model)
                    sims.extend(model_sims)
                    vizs.extend(model_vizs)
                except ModelIoError:
                    unimportable_models.append(model_result['id'])
                except SimIoError:
                    unimportable_sims.append(model_result['id'])

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

                # todo: simulate models

                if len(models) == self._max_models:
                    break

        if unimportable_models:
            warnings.warn('Unable import the following models:\n  {}'.format('\n  '.join(sorted(unimportable_models))), BiomodelsIoWarning)
        if unimportable_sims:
            warnings.warn('Unable import simulations for the following models:\n  {}'.format(
                '\n  '.join(sorted(unimportable_sims))), BiomodelsIoWarning)
        if unvisualizable_models:
            warnings.warn('Unable visualize the following models:\n  {}'.format(
                '\n  '.join(sorted(unvisualizable_models))), BiomodelsIoWarning)

        return (models, sims, vizs)

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
            :obj:`list` of :obj:`Visualization`: information about visualizations
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
        vizs = []
        num_sim_files = 0
        for file_metadata in files_metadata['additional']:
            if file_metadata['name'].endswith('.sedml'):
                num_sim_files += 1
                local_path = os.path.join(self._cache_dir, '{}-{}.sedml'.format(model.id, num_sim_files))
                with open(local_path, 'wb') as file:
                    file.write(self.get_model_file(id, file_metadata['name']))

                model_sims, model_viz = read_sim(local_path, ModelFormat.sbml, SimFormat.sedml)

                model_files = set([sim.model.file.name for sim in model_sims]).difference(set(['model']))
                assert len(model_files) <= 1, 'Each simulation must use the same model'

                for sim in model_sims:
                    sim.id = '{}-sim-{}'.format(model.id, len(sims))
                    sim.name = file_metadata['name'][0:-6]
                    sim.description = file_metadata['description']
                    sim.identifiers = [Identifier(namespace='biomodels.db', id=metadata['publicationId'])]
                    sim.references = copy.deepcopy(model.references)
                    sim.authors = copy.deepcopy(model.authors)
                    sim.license = License.cc0
                    sim.model.id = model.id
                    sim.model.name = model.name
                    sim.model.file = None
                    sims.append(sim)

                if model_viz:
                    model_viz.id = '{}-viz-{}'.format(model.id, len(vizs) + 1)
                    model_viz.name = file_metadata['name'][0:-6]
                    model_viz.description = file_metadata['description']
                    model_viz.identifiers = [Identifier(namespace='biomodels.db', id=metadata['publicationId'])]
                    model_viz.references = copy.deepcopy(model.references)
                    model_viz.authors = copy.deepcopy(model.authors)
                    model_viz.license = License.cc0
                    vizs.append(model_viz)

        if len(sims) == 1:
            sims[0].id = '{}-sim'.format(model.id)
            os.rename(
                os.path.join(self._cache_dir, '{}-{}.sedml'.format(model.id, 1)),
                os.path.join(self._cache_dir, '{}.sedml'.format(model.id)))

        if len(vizs) == 1:
            vizs[0].id = '{}-viz'.format(model.id)

        return (model, sims, vizs)

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

    def submit_models(self, models, sims, vizs):
        """ Post models and simulations to BioSimulations

        Args:
            models (:obj:`list` of :obj:`Model`):
            sims (:obj:`list` of :obj:`Simulation`): simulations
            vizs (:obj:`list` of :obj:`Visualization`): visualization
        """
        api_client = ApiClient(_dry_run=self._dry_run)
        api_client.login()

        for model in models:
            api_client.exec('post', '/models/' + model.id, data=model.to_json())

        for sim in sims:
            api_client.exec('post', '/simulations/' + sim.id, data=sim.to_json())

        for viz in vizs:
            api_client.exec('post', '/visualization/' + viz.id, data=viz.to_json())

    def write_data(self, models, sims, vizs, stats):
        """ Save models and simulations to JSON files

        Args:
            models (:obj:`list` of :obj:`Model`): models
            sims (:obj:`list` of :obj:`Simulation`): simulations
            vizs (:obj:`list` of :obj:`Visualization`): visualization
            stats (:obj:`dict`): statistics of the models
        """
        filename = os.path.join(self._cache_dir, 'biomodels.models.json')
        with open(filename, 'w') as file:
            json.dump([model.to_json() for model in models], file)

        filename = os.path.join(self._cache_dir, 'biomodels.simulations.json')
        with open(filename, 'w') as file:
            json.dump([sim.to_json() for sim in sims], file)

        filename = os.path.join(self._cache_dir, 'biomodels.visualizations.json')
        with open(filename, 'w') as file:
            json.dump([viz.to_json() for viz in vizs], file)

        filename = os.path.join(self._cache_dir, 'biomodels.stats.json')
        with open(filename, 'w') as file:
            json.dump(stats, file)

    def read_data(self):
        """ Read models, simulations, and visualizations from JSON files

        Returns:
            :obj:`list` of :obj:`Model`: models
            :obj:`list` of :obj:`Simulation`: simulations
            :obj:`list` of :obj:`Visualization`: visualizations
            :obj:`dict`: stats about the models
        """
        filename = os.path.join(self._cache_dir, 'biomodels.models.json')
        with open(filename, 'r') as file:
            models = [Model.from_json(model) for model in json.load(file)]

        filename = os.path.join(self._cache_dir, 'biomodels.simulations.json')
        with open(filename, 'r') as file:
            sims = [Simulation.from_json(sim) for sim in json.load(file)]

        filename = os.path.join(self._cache_dir, 'biomodels.visualizations.json')
        with open(filename, 'r') as file:
            vizs = [Visualization.from_json(viz) for viz in json.load(file)]

        filename = os.path.join(self._cache_dir, 'biomodels.stats.json')
        with open(filename, 'r') as file:
            stats = json.load(file)

        return (models, sims, vizs, stats)

    def get_stats(self, models, sims, vizs):
        """ Calculate statistics about the imported models

        Args:
            models (:obj:`list` of :obj:`Model`): models
            sims (:obj:`list` of :obj:`Simulation`): simulations
            vizs (:obj:`list` of :obj:`Visualization`): visualizations

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
            },
            'vizs': {
                'total': len(vizs),
            },
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


class BiomodelsIoWarning(UserWarning):
    """ BioModels IO warning """
    pass
