""" Tests of data model for models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import (Identifier, JournalReference,
                                                    License, OntologyTerm, Person, RemoteFile, Taxon, Type)
from Biosimulations_format_utils.biomodel.data_model import (Biomodel, BiomodelParameter, BiomodelVariable, BiomodelFormat)
import unittest


class BiomodelDataModelTestCase(unittest.TestCase):
    def test_Biomodel(self):
        model = Biomodel(
            id='model_1',
            name='model 1',
            file=RemoteFile(name='model.xml', type='application/sbml+xml'),
            image=RemoteFile(name='model.png', type='image/png'),
            description='description',
            format=BiomodelFormat.sbml.value,
            framework=OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                                   description='KLU is a software package and an algorithm ...',
                                   iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497'),
            taxon=Taxon(id=9606, name='Homo sapiens'),
            tags=['a', 'b', 'c'],
            identifiers=[Identifier(namespace='biomodels.db', id='BIOMD0000000924')],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            parameters=[BiomodelParameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
            variables=[BiomodelVariable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
        )
        self.assertEqual(Biomodel.from_json(model.to_json()), model)

    def test_Parameter(self):
        param = BiomodelParameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])
        self.assertEqual(BiomodelParameter.from_json(param.to_json()), param)
        self.assertEqual(BiomodelParameter.sort_key(param), param.id)

    def test_Variable(self):
        var = BiomodelVariable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])
        self.assertEqual(BiomodelVariable.from_json(var.to_json()), var)
        self.assertEqual(BiomodelVariable.sort_key(var), var.id)
