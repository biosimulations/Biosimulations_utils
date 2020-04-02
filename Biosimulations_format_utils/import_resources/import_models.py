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
import math
import os
import re
import requests
import requests.adapters
import requests_cache
import xml.etree.ElementTree


class ImportBioModels(object):
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
        """
        models = self.get_models()
        self.submit_models(models)
        return models

    def get_models(self):
        """ Get models from BioModels

        Returns:
            :obj:`list` of :obj:`Model`: list of metadata about each model
        """
        models = []
        num_models = min(self._max_models, self.get_num_models())
        print('Importing {} models'.format(num_models))
        for i_batch in range(int(math.ceil(num_models / self.NUM_MODELS_PER_BATCH))):
            results = self.get_model_batch(num_results=self.NUM_MODELS_PER_BATCH, i_batch=i_batch)
            for model_result in results['models']:
                print('  {}. {}: {}'.format(len(models) + 1, model_result['id'], model_result['name']))
                try:
                    models.append(self.get_model(model_result['id']))
                except ModelIoError:
                    pass
                if len(models) == self._max_models:
                    break
        return models

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
        """
        metadata = self.get_model_metadata(id)

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
                if pub_xml:
                    pub_ids_xml = pub_xml.find('PubmedData').find('ArticleIdList').findall('ArticleId')
                    for pub_id_xml in pub_ids_xml:
                        if pub_id_xml.get('IdType') == 'doi':
                            doi = pub_id_xml.text
                            break

                authors = []
                authors_str = ''
                if pub_xml:
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

            refs = [
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
            refs = []

        filename = self.get_model_files_metadata(id)['main'][0]['name']
        local_path = os.path.join(self._cache_dir, filename)
        with open(local_path, 'wb') as file:
            file.write(self.get_model_file(id, filename))

        model = read_model(local_path, format=ModelFormat.sbml)
        model.id = id
        model.name = metadata['name']
        model.file = RemoteFile(
            name=filename,
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
        model.refs = refs
        model.authors = authors
        model.license = License.cc0
        return model

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

    def submit_models(self, models):
        """ Post models to BioSimulations

        Args:
            models (:obj:`list` of :obj:`obj`):
        """
        for model in models:
            # Todo: submit models to BioSimulations
            # requests.post(self.BIOSIMULATIONS_ENDPOINT)
            pass
