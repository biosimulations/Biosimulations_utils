""" Tests of reading and writing OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulations_utils.archive import write_archive, read_archive
from biosimulations_utils.archive.core import ArchiveIoError
from biosimulations_utils.archive.data_model import Archive, ArchiveFile, ArchiveFormat
from biosimulations_utils.data_model import Format, Person
from biosimulations_utils.biomodel.data_model import BiomodelFormat
from biosimulations_utils.simulation.data_model import SimulationFormat
from unittest import mock
import datetime
import dateutil.tz
import libcombine
import os
import shutil
import tempfile
import unittest


class OmexArchiveTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test(self):
        archive_dir1 = os.path.join(self.dirname, 'dir1')
        archive_dir2 = os.path.join(self.dirname, 'dir2')
        archive_filename = os.path.join(self.dirname, 'archive.omex')

        model = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">'
            '<model id="case_01" name="case_01">'
            '</model>'
            '</sbml>'
        )

        os.makedirs(os.path.join(archive_dir1, 'models'))
        with open(os.path.join(archive_dir1, 'models', 'model.xml'), 'w') as file:
            file.write(model)

        now = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        archive = Archive(
            files=[
                ArchiveFile(filename='./models/model.xml', format=BiomodelFormat.sbml.value, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')], created=now, updated=now),
                ArchiveFile(filename='./sims/sim.xml', format=SimulationFormat.sedml.value, description='Description1',
                            authors=[Person(first_name='John', last_name='Doe')], created=None, updated=now),
                ArchiveFile(filename='./sims/sim2.xml', format=None, description='Description2',
                            authors=[Person(first_name='Jane', last_name='Doe')], created=None, updated=now),
                ArchiveFile(filename='./sims/sim3.xml', format=Format(spec_url='https://myspec.com'), description='Description3',
                            authors=[Person(first_name='Jack', last_name='Doe')], created=now, updated=None),
            ],
            description='Description',
            authors=[Person(first_name='John', last_name='Doe')],
            format=ArchiveFormat.combine.value,
            created=now,
            updated=now,
        )
        archive.master_file = archive.files[0]

        write_archive(archive, archive_dir1, archive_filename)

        archive_2 = read_archive(archive_filename, archive_dir2)
        self.assertEqual(archive_2, archive)
        with open(os.path.join(archive_dir2, 'models', 'model.xml'), 'r') as file:
            self.assertEqual(file.read(), model)

        # test error handling
        with self.assertRaisesRegex(NotImplementedError, "is not supported"):
            write_archive(archive, archive_dir1, archive_filename, format=mock.Mock(name='None'))
        with self.assertRaisesRegex(NotImplementedError, "is not supported"):
            read_archive(archive_filename, archive_dir2, format=mock.Mock(name='None'))

        with self.assertRaisesRegex(ArchiveIoError, "Invalid COMBINE archive"):
            read_archive('non-existant-file', archive_dir2)

        # test multiple update dates
        archive_comb = libcombine.CombineArchive()

        desc_comb = libcombine.OmexDescription()
        desc_comb.setAbout('.')
        desc_comb.setDescription('description')

        date_comb = libcombine.Date()
        date_comb.setDateAsString(now.strftime('%Y-%m-%dT%H:%M:%SZ'))
        desc_comb.getModified().append(date_comb)

        date_comb = libcombine.Date()
        date_comb.setDateAsString((now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ'))
        desc_comb.getModified().append(date_comb)

        archive_comb.addMetadata('.', desc_comb)

        archive_comb.addFile(
            os.path.join(archive_dir1, './models/model.xml'),
            './models/model.xml',
            BiomodelFormat.sbml.value.spec_url,
            True
        )

        archive_filename_2 = os.path.join(self.dirname, 'archive2.omex')
        archive_comb.writeToFile(archive_filename_2)
        archive_comb.writeToFile(archive_filename_2)

        archive_dir3 = os.path.join(self.dirname, 'dir3')
        archive_3 = read_archive(archive_filename_2, archive_dir3)
        archive_3.updated > archive_2.updated
