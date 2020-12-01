""" Tests of data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulations_utils.chart.data_model import Chart, ChartDataField, ChartDataFieldShape, ChartDataFieldType
from biosimulations_utils.data_model import (AccessLevel, Format, Identifier, JournalCitation,
                                             License, OntologyTerm, Person, PrimaryResourceMetadata, RemoteFile,
                                             ResourceMetadata, ResourceReferences, Taxon, Type, User)
from biosimulations_utils.biomodel.data_model import Biomodel, BiomodelParameter, BiomodelVariable, BiomodelFormat
from biosimulations_utils.simulation.data_model import TimecourseSimulation, SimulationResult
from biosimulations_utils.visualization.data_model import Visualization, VisualizationLayoutElement, VisualizationDataField
import datetime
import dateutil
import inflect
import json
import requests
import unittest


class DataModelTestCase(unittest.TestCase):
    def test_Format(self):
        format = BiomodelFormat.sbml.value
        self.assertEqual(Format.from_json(format.to_json()), format)
        self.assertEqual(Format.sort_key(format), (format.id, format.name, format.version, format.edam_id, format.url,
                                                   format.spec_url, format.mimetype, format.extension, format.sed_urn))

    def test_Identifier(self):
        id = Identifier(namespace='biomodels.db', id='BIOMD0000000924')
        self.assertEqual(Identifier.from_json(id.to_json()), id)

        self.assertEqual(Identifier.sort_key(id), (id.namespace, id.id, None))

    def test_JournalReference(self):
        ref = JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                              volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX')
        self.assertEqual(JournalCitation.from_json(ref.to_json()), ref)
        self.assertEqual(JournalCitation.sort_key(ref), (ref.authors, ref.title,
                                                         ref.journal, ref.volume, ref.issue, ref.pages, ref.year, ref.doi))

    def test_OntologyTerm(self):
        term = OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                            description='KLU is a software package and an algorithm ...',
                            iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497')
        self.assertEqual(OntologyTerm.from_json(term.to_json()), term)
        self.assertEqual(OntologyTerm.sort_key(term), (term.ontology, term.id, term.name, term.description, term.iri))

    def test_Person(self):
        person = Person(first_name='John', middle_name='C', last_name='Doe')
        self.assertEqual(Person.from_json(person.to_json()), person)
        self.assertEqual(Person.sort_key(person), (person.last_name, person.first_name, person.middle_name))

    def test_RemoteFile(self):
        file = RemoteFile(id='model-file', name='model.xml', type='application/sbml+xml', size=1000)
        self.assertEqual(RemoteFile.from_json(file.to_json()), file)

        json = file.to_json()
        json['data']['type'] = None
        with self.assertRaisesRegex(ValueError, '`type`'):
            RemoteFile.from_json(json)

    def test_Taxon(self):
        taxon = Taxon(id=9606, name='Homo sapiens')
        self.assertEqual(Taxon.from_json(taxon.to_json()), taxon)

    def test_User(self):
        user = User(id='user-id')
        self.assertEqual(User.from_json(user.to_json()), user)

        json = user.to_json()
        json['data']['type'] = None
        with self.assertRaisesRegex(ValueError, '`type`'):
            User.from_json(json)

    def test_ResourceMetadata(self):
        now = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        md = ResourceMetadata(
            version='1.0.0',
            created=now,
            updated=now,
        )
        self.assertEqual(ResourceMetadata.from_json(md.to_json()), md)

    def test_PrimaryResourceMetadata(self):
        md = PrimaryResourceMetadata(
            name='name',
            # image=RemoteFile(id='thumbnail'),
            summary='summary',
            description='description',
            tags=['tag1', 'tag2'],
            references=ResourceReferences(
                identifiers=[Identifier(namespace='biomodels', id='BIOMD0000000924')],
                citations=[
                    JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                    volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
                ],
                doi='10.0.1/XXX',
            ),
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            # parent=Biomodel(id='biomodel-0'),
            license=License.cc0,
            # owner=User(id='user-id'),
            access_level=AccessLevel.private,
        )
        self.assertEqual(PrimaryResourceMetadata.from_json(md.to_json()), md)

    def test_ResourceReferences(self):
        refs = ResourceReferences(
            identifiers=[Identifier(namespace='biomodels', id='BIOMD0000000924')],
            citations=[
                JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            doi='10.0.1/XXX')
        self.assertEqual(refs.from_json(refs.to_json()), refs)


@unittest.skip('API is in development')
class ApiConsistencyTestCase(unittest.TestCase):
    SPEC = 'https://api.biosimulations.dev/openapi.json'

    @classmethod
    def setUpClass(cls):
        response = requests.get(cls.SPEC)
        response.raise_for_status()
        cls.api_schemas = response.json()['components']['schemas']

    @unittest.expectedFailure
    def test_model(self):
        # todo: align TypeScript data model with this Python data model and remove @unittest.expectedFailure()
        model = Biomodel(
            id='model_1',
            name='model 1',
            file=RemoteFile(id='model_1-file', name='model.xml', type='application/sbml+xml'),
            image=RemoteFile(id='model_1-thumbnail', name='model.png', type='image/png'),
            description='description',
            format=BiomodelFormat.sbml.value,
            framework=OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                                   description='KLU is a software package and an algorithm ...',
                                   iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497'),
            taxon=Taxon(id=9606, name='Homo sapiens'),
            tags=['a', 'b', 'c'],
            references=ResourceReferences(
                identifiers=[Identifier(namespace='biomodels.db', id='BIOMD0000000924')],
                citations=[
                    JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                    volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
                ]
            ),
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            parameters=[BiomodelParameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
            variables=[BiomodelVariable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
        )
        py = model.to_json()

        api = {}
        for schema in self.api_schemas['Biomodel']['allOf']:
            for key, val in schema['properties'].items():
                api[key] = val

        errors = self.get_differences_from_api(py, api)
        if errors:
            raise Exception('Data model for `Biomodel` is not consistent with API:\n  Biomodel:\n    ' + '\n    '.join(errors))

    @unittest.expectedFailure
    def test_sim(self):
        # todo: align TypeScript data model with this Python data model and remove @unittest.expectedFailure()
        with open('tests/fixtures/simulation.json', 'rb') as file:
            py = json.load(file)

        api = {}
        for schema in self.api_schemas['Simulation']['allOf']:
            for key, val in schema['properties'].items():
                api[key] = val

        errors = self.get_differences_from_api(py, api)
        if errors:
            raise Exception('Data model for `Simulation` is not consistent with API:\n  Simulation:\n    ' + '\n    '.join(errors))

    def test_chart(self):
        py = Chart(id='chart-type-1').to_json()

        api = {}
        for schema in self.api_schemas['Chart']['allOf']:
            for key, val in schema['properties'].items():
                api[key] = val

        errors = self.get_differences_from_api(py, api)
        if errors:
            raise Exception('Data model for `Chart` is not consistent with API:\n  Chart:\n    ' + '\n    '.join(errors))

    @unittest.expectedFailure
    def test_viz(self):
        py = Visualization(
            id='viz_1',
            name='viz 1',
            image=RemoteFile(id='viz-thumbnail', name='viz.png', type='image/png'),
            description='description',
            tags=['a', 'b', 'c'],
            references=ResourceReferences(
                identifiers=[Identifier(namespace='biomodels.db', id='XXX')],
                citations=[
                    JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                    volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
                ]
            ),
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            format=Format(name='Vega', version='5.10.1', url='https://vega.github.io/vega/'),
            columns=3,
            layout=[
                VisualizationLayoutElement(
                    chart=Chart(id='line'),
                    data=[
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 1',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-1')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-1')),
                            ],
                        ),
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 0',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-4'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-3'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-4')),
                            ],
                        ),
                    ],
                ),
                VisualizationLayoutElement(
                    chart=Chart(id='area'),
                    data=[
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 1',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-1')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-2')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-1')),
                            ],
                        ),
                        VisualizationDataField(
                            data_field=ChartDataField(name='field 0',
                                                      shape=ChartDataFieldShape.array,
                                                      type=ChartDataFieldType.static),
                            simulation_results=[
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-4'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-3'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-2'), variable=BiomodelVariable(id='var-4')),
                                SimulationResult(simulation=TimecourseSimulation(
                                    id='sim-1'), variable=BiomodelVariable(id='var-4')),
                            ],
                        ),
                    ],
                )
            ],
        ).to_json()

        api = {}
        for schema in self.api_schemas['Visualization']['allOf']:
            for key, val in schema['properties'].items():
                api[key] = val

        errors = self.get_differences_from_api(py, api)
        if errors:
            raise Exception('Data model for `Visualization` is not consistent with API:\n  Visualization:\n    ' + '\n    '.join(errors))

    def get_differences_from_api(self, py, api, path=''):
        errors = []

        infect_engine = inflect.engine()

        for key, val in py.items():
            if key not in api:
                errors.append('{}: not in API'.format(path + key))
            else:
                if isinstance(val, list):
                    if isinstance(val[0], dict):
                        if 'items' not in api[key]:
                            errors.append('{}: API does not use an array'.format(path + key))
                        elif 'properties' not in api[key]['items']:
                            singular_key = infect_engine.singular_noun(key) or key
                            errors.append('{}'.format(path + key))
                            errors.append('  {}: API does not use an array of dictionaries'.format(path + singular_key))
                        else:
                            prop_errors = self.get_differences_from_api(val[0], api[key]['items']['properties'], path=path + '    ')
                            if prop_errors:
                                singular_key = infect_engine.singular_noun(key) or key
                                errors.append('{}'.format(path + key))
                                errors.append('  {}'.format(path + singular_key))
                                errors.extend(prop_errors)
                elif isinstance(val, dict):
                    if 'properties' not in api[key]:
                        errors.append('{}: API does not use a dictionary'.format(path + key))
                    else:
                        prop_errors = self.get_differences_from_api(val, api[key]['properties'], path=path + '  ')
                        if prop_errors:
                            errors.append('{}'.format(path + key))
                            errors.extend(prop_errors)

        return errors
