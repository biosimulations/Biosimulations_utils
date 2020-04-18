""" Classes for reading and writing OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import ArchiveWriter, ArchiveReader, ArchiveIoError
from .data_model import Archive, ArchiveFile, ArchiveFormat
from ..data_model import Format, Person
from ..biomodel.data_model import BiomodelFormat
from ..simulation.data_model import SimulationFormat
from ..utils import get_enum_format_by_attr
import copy
import dateutil.parser
import libcombine
import os


__all__ = ['CombineArchiveWriter', 'CombineArchiveReader']


class CombineArchiveWriter(ArchiveWriter):
    """ Writer for COMBINE/OMEX archives """

    def run(self, archive, in_dir, out_file):
        """ Write an archive to a file

        Args:
            archive (:obj:`Archive`): description of archive
            in_dir (:obj:`str`): directory which contains the files in the archive
            out_file (:obj:`str`): path to save archive

        Raises:
            :obj:`AssertionError`: if files could not be added to the archive or the archive could not be
                saved
        """
        # instantiate archive
        archive_comb = libcombine.CombineArchive()

        # set metadata about archive
        self._write_metadata(archive, archive_comb, '.')

        # add files to archive
        for file in archive.files:
            assert archive_comb.addFile(
                os.path.join(in_dir, file.filename),
                file.filename,
                file.format.spec_url if file.format else '',
                file is archive.master_file
            )
            self._write_metadata(file, archive_comb, file.filename)

        # delete file if it already exists because libcombine appends to files rather then overwriting them
        if os.path.isfile(out_file):
            os.remove(out_file)

        # save archive to a file        
        assert archive_comb.writeToFile(out_file)

    def _write_metadata(self, obj, archive_comb, filename):
        """ Write metadata about an archive or a file in an archive
        Args:
            obj (:obj:`Archive` or :obj:`ArchiveFile`): archive or file in an archive
            archive_comb (:obj:`libcombine.CombineArchive`): archive
            filename (:obj:`str`): path of object with archive
        """
        desc_comb = libcombine.OmexDescription()
        desc_comb.setAbout(filename)
        if obj.description:
            desc_comb.setDescription(obj.description)
        for author in obj.authors:
            creator_comb = libcombine.VCard()
            if author.first_name:
                creator_comb.setGivenName(author.first_name)
            if author.last_name:
                creator_comb.setFamilyName(author.last_name)
            desc_comb.addCreator(creator_comb)
        if obj.created:
            date_comb = libcombine.Date()
            date_comb.setDateAsString(obj.created.strftime('%Y-%m-%dT%H:%M:%SZ'))
            desc_comb.setCreated(date_comb)
        if obj.updated:
            date_comb = libcombine.Date()
            date_comb.setDateAsString(obj.updated.strftime('%Y-%m-%dT%H:%M:%SZ'))
            desc_comb.getModified().append(date_comb)
        archive_comb.addMetadata(filename, desc_comb)


class CombineArchiveReader(ArchiveReader):
    """ Reader for COMBINE/OMEX archives """

    NONE_DATETIME = '2000-01-01T00:00:00Z'

    def run(self, in_file, out_dir):
        """ Read an archive from a file

        Args:
            in_file (:obj:`str`): path to save archive
            out_dir (:obj:`str`): directory which contains the files in the archive

        Returns:
            :obj:`Archive`: description of archive

        Raises:
            :obj:`ArchiveIoError`: archive is invalid
        """
        archive_comb = libcombine.CombineArchive()
        if not archive_comb.initializeFromArchive(in_file):
            raise ArchiveIoError("Invalid COMBINE archive")

        # instantiate archive
        archive = Archive(format=ArchiveFormat.combine.value)

        # read metadata
        self._read_metadata(archive_comb, '.', archive)

        # read files
        for filename in archive_comb.getAllLocations():
            filename = filename.c_str()
            file_comb = archive_comb.getEntryByLocation(filename)

            if file_comb.isSetFormat():
                spec_url = file_comb.getFormat()
                format = get_enum_format_by_attr(BiomodelFormat, 'spec_url', spec_url)
                if not format:
                    format = get_enum_format_by_attr(SimulationFormat, 'spec_url', spec_url)
                if format:
                    format = copy.copy(format)
                else:
                    format = Format(spec_url=spec_url)
            else:
                format = None

            file = ArchiveFile(
                filename=filename,
                format=format,
            )
            self._read_metadata(archive_comb, filename, file)
            archive.files.append(file)

        file_comb = archive_comb.getMasterFile()
        if file_comb:
            filename = file_comb.getLocation()
            archive.master_file = next(file for file in archive.files if file.filename == filename)

        # extract files
        archive_comb.extractTo(out_dir)

        # return information about archive
        return archive

    def _read_metadata(self, archive_comb, filename, obj):
        """ Read metadata about an archive or a file in an archive

        Args:
            archive_comb (:obj:`libcombine.CombineArchive`): archive
            filename (:obj:`str`): path to object within archive
            obj (:obj:`Archive` of :obj:`ArchiveFile`): object to add metadata to
        """
        desc_comb = archive_comb.getMetadataForLocation(filename)
        if not desc_comb.isEmpty():
            obj.description = desc_comb.getDescription() or None

            for creator_comb in desc_comb.getCreators():
                obj.authors.append(Person(
                    first_name=creator_comb.getGivenName() or None,
                    last_name=creator_comb.getFamilyName() or None,
                ))

            created_comb = desc_comb.getCreated().getDateAsString()
            if created_comb == self.NONE_DATETIME:
                obj.created = None
            else:
                obj.created = dateutil.parser.parse(created_comb)

            obj.updated = None
            for modified_comb in desc_comb.getModified():
                updated = dateutil.parser.parse(modified_comb.getDateAsString())
                if obj.updated:
                    obj.updated = max(obj.updated, updated)
                else:
                    obj.updated = updated
