""" Tests of data model for archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.data_model import Person
from Biosimulations_format_utils.model.data_model import ModelFormat
from Biosimulations_format_utils.archive.data_model import Archive, ArchiveFile, ArchiveFormat
import datetime
import unittest


class ArchiveDataModelTestCase(unittest.TestCase):
    def test_Archive(self):
        now = datetime.datetime.now()
        archive1 = Archive(
            files=[
                ArchiveFile(filename='./models/model.xml',
                            format=ModelFormat.sbml,
                            description='Description',
                            authors=[Person(first_name='John', last_name='Doe')],
                            created=now,
                            updated=now),
            ],
            description='Description',
            authors=[Person(first_name='John', last_name='Doe')],
            format=ArchiveFormat.combine.value,
            created=now,
            updated=now)
        archive1.master_file = archive1.files[0]

        archive2 = Archive(
            files=[
                ArchiveFile(filename='./models/model.xml',
                            format=ModelFormat.sbml, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')],
                            created=now,
                            updated=now),
            ],
            description='Description',
            authors=[Person(first_name='John', last_name='Doe')],
            format=ArchiveFormat.combine.value,
            created=now,
            updated=now)
        archive2.master_file = archive2.files[0]

        archive3 = Archive(
            files=[
                ArchiveFile(filename='./models/model.xml',
                            format=ModelFormat.sbml,
                            description='Description',
                            authors=[Person(first_name='John', last_name='Doe')],
                            created=now,
                            updated=now),
            ],
            description='Description',
            authors=[Person(first_name='John', last_name='Doe')],
            format=ArchiveFormat.combine.value,
            created=now,
            updated=now)

        self.assertEqual(archive1, archive2)
        self.assertNotEqual(archive1, archive3)

    def test_ArchiveFile(self):
        now = datetime.datetime.now()
        file1 = ArchiveFile(filename='./models/model.xml',
                            format=ModelFormat.sbml, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')],
                            created=now,
                            updated=now)
        file2 = ArchiveFile(filename='./models/model.xml',
                            format=ModelFormat.sbml, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')],
                            created=now,
                            updated=now)
        file3 = ArchiveFile(filename='./models/model2.xml',
                            format=ModelFormat.sbml, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')],
                            created=now,
                            updated=now)
        self.assertEqual(file1, file2)
        self.assertNotEqual(file1, file3)
        self.assertEqual(ArchiveFile.sort_key(file1), ('./models/model.xml', 'sbml', 'Description', (('Doe', 'John', None, ),), now, now))
