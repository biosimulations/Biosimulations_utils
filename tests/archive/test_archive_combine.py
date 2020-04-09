""" Tests of reading and writing OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.archive import write_archive, read_archive
from Biosimulations_format_utils.archive.core import ArchiveIoError
from Biosimulations_format_utils.archive.data_model import Archive, ArchiveFile, ArchiveFormat
from Biosimulations_format_utils.data_model import Person
from Biosimulations_format_utils.biomodel.data_model import BiomodelFormat
from Biosimulations_format_utils.simulation.data_model import SimulationFormat
from unittest import mock
import datetime
import dateutil.tz
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

        now = datetime.datetime.utcnow()
        now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second, tzinfo=dateutil.tz.UTC)
        archive = Archive(
            files=[
                ArchiveFile(filename='./models/model.xml', format=BiomodelFormat.sbml.value, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')], created=now, updated=now),
                ArchiveFile(filename='./sims/sim.xml', format=SimulationFormat.sedml.value, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')], created=None, updated=now),
                ArchiveFile(filename='./sims/sim2.xml', format=None, description='Description',
                            authors=[Person(first_name='John', last_name='Doe')], created=None, updated=now),
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

        with self.assertRaisesRegex(ArchiveIoError, "Invalid OMEX archive"):
            read_archive('non-existant-file', archive_dir2)
