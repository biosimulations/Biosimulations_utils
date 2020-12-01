""" Tests of data model for models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulations_utils.data_model import (Identifier, JournalCitation, License, OntologyTerm, Person, RemoteFile,
                                             PrimaryResourceMetadata, ResourceMetadata, ResourceReferences, Taxon, Type, User)
from biosimulations_utils.biomodel.data_model import (Biomodel, BiomodelParameter, BiomodelVariable, BiomodelFormat)
import datetime
import dateutil.tz
import unittest


class BiomodelDataModelTestCase(unittest.TestCase):
    def test_Biomodel(self):
        model = Biomodel(
            id='model_1',
            file=RemoteFile(id='model_1-file'),
            format=BiomodelFormat.sbml.value,
            framework=OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                                   description='KLU is a software package and an algorithm ...',
                                   iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497'),
            taxon=Taxon(id=9606, name='Homo sapiens'),
            parameters=[BiomodelParameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
            variables=[BiomodelVariable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
            metadata=PrimaryResourceMetadata(
                name='model 1',
                image=RemoteFile(id='model_1-thumbnail'),
                summary='summary',
                description='description',
                tags=['a', 'b', 'c'],
                references=ResourceReferences(
                    identifiers=[Identifier(namespace='biomodels.db', id='BIOMD0000000924')],
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
                parent=Biomodel(id='model_0'),
                license=License.cc0,
                owner=User(id='user-0'),
            ),
            _metadata=ResourceMetadata(
                version=3,
                created=datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC),
                updated=datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC),
            ),
        )
        model2 = Biomodel.from_json(model.to_json())
        self.assertEqual(model2, model)

    def test_Parameter(self):
        param = BiomodelParameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])
        self.assertEqual(BiomodelParameter.from_json(param.to_json()), param)
        self.assertEqual(BiomodelParameter.sort_key(param), param.id)

    def test_Variable(self):
        var = BiomodelVariable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])
        self.assertEqual(BiomodelVariable.from_json(var.to_json()), var)
        self.assertEqual(BiomodelVariable.sort_key(var), var.id)
