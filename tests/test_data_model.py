""" Tests of data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Format, Identifier, JournalReference, OntologyTerm, Person, RemoteFile, Taxon
import unittest


class DataModelTestCase(unittest.TestCase):
    def test_Format(self):
        format = Format(name='SBML', version='L3V2', edam_id='format_2585', url='http://sbml.org')
        self.assertEqual(Format.from_json(format.to_json()), format)

    def test_Identifier(self):
        id = Identifier(namespace='biomodels.db', id='BIOMD0000000924')
        self.assertEqual(Identifier.from_json(id.to_json()), id)

        self.assertEqual(Identifier.sort_key(id), (id.namespace, id.id))

    def test_JournalReference(self):
        ref = JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                               volume=10, num=3, pages='1-10', year=2020, doi='10.1016/XXXX')
        self.assertEqual(JournalReference.from_json(ref.to_json()), ref)
        self.assertEqual(JournalReference.sort_key(ref), (ref.authors, ref.title,
                                                          ref.journal, ref.volume, ref.num, ref.pages, ref.year, ref.doi))

    def test_OntologyTerm(self):
        term = OntologyTerm(ontology='KISAO', id='0000497', name='KLU',
                            description='KLU is a software package and an algorithm ...',
                            iri='http://www.biomodels.net/kisao/KISAO#KISAO_0000497')
        self.assertEqual(OntologyTerm.from_json(term.to_json()), term)

    def test_Person(self):
        person = Person(first_name='John', middle_name='C', last_name='Doe')
        self.assertEqual(Person.from_json(person.to_json()), person)
        self.assertEqual(Person.sort_key(person), (person.last_name, person.first_name, person.middle_name))

    def test_RemoteFile(self):
        file = RemoteFile(name='model.xml', type='application/sbml+xml', size=1000)
        self.assertEqual(RemoteFile.from_json(file.to_json()), file)

    def test_Taxon(self):
        taxon = Taxon(id=9606, name='Homo sapiens')
        self.assertEqual(Taxon.from_json(taxon.to_json()), taxon)
