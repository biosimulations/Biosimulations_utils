""" Tests of data model for models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import (Format, Identifier, JournalReference,
                                                    License, OntologyTerm, Person, RemoteFile, Taxon, Type)
from Biosimulations_format_utils.model.data_model import Model, Parameter, Variable
import unittest


class ModelDataModelTestCase(unittest.TestCase):
    def test_Model(self):
        model = Model(
            id='model_1',
            name='model 1',
            file=RemoteFile(name='model.xml', type='application/sbml+xml'),
            image=RemoteFile(name='model.png', type='image/png'),
            description='description',
            format=Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org'),
            framework=OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                                   description='KLU is a software package and an algorithm ...',
                                   iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497'),
            taxon=Taxon(id=9606, name='Homo sapiens'),
            tags=['a', 'b', 'c'],
            identifiers=[Identifier(namespace='biomodels.db', id='BIOMD0000000924')],
            refs=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, num=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            parameters=[Parameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
            variables=[Variable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])],
        )
        self.assertEqual(Model.from_json(model.to_json()), model)

    def test_Parameter(self):
        param = Parameter(id='k_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])
        self.assertEqual(Parameter.from_json(param.to_json()), param)
        self.assertEqual(Parameter.sort_key(param), param.id)

    def test_Variable(self):
        var = Variable(id='species_1', type=Type.float, identifiers=[Identifier(namespace='a', id='x')])
        self.assertEqual(Variable.from_json(var.to_json()), var)
        self.assertEqual(Variable.sort_key(var), var.id)
