""" Data model for archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Person
from ..model.data_model import ModelFormat  # noqa: F401
from ..simulation.data_model import SimFormat  # noqa: F401
import datetime
import wc_utils.util.enumerate

__all__ = ['ArchiveFormat', 'Archive', 'ArchiveFile']


class ArchiveFormat(str, wc_utils.util.enumerate.CaseInsensitiveEnum):
    """ Simulation experiment formats """
    OMEX = 'http://identifiers.org/combine.specifications/omex'


class Archive(object):
    """ An archive archive

    Attributes:
        master_file (:obj:`ArchiveFile`): master file of archive
        files (:obj:`list` of `:obj:`ArchiveFile`): files in archive
        description (:obj:`str`): description
        authors (:obj:`list` of :obj:`Person`): authors of the archive
        created (:obj:`datetime.datetime`): date archive was created
        updated (:obj:`datetime.datetime`): date archive was last updated
    """

    def __init__(self, master_file=None, files=None, description=None, authors=None, created=None, updated=None):
        """
        Args:
            master_file (:obj:`ArchiveFile`, optional): master file of archive
            files (:obj:`list` of `:obj:`ArchiveFile`, optional): files in archive
            description (:obj:`str`, optional): description
            authors (:obj:`list` of :obj:`Person`, optional): authors of the archive
            created (:obj:`datetime.datetime`, optional): date archive was created
            updated (:obj:`datetime.datetime`, optional): date archive was last updated
        """
        self.master_file = master_file
        self.files = files or []
        self.description = description
        self.authors = authors or []
        self.created = created or datetime.datetime.now()
        self.updated = updated or self.created

    def __eq__(self, other):
        """ Determine if two archives are semantically equal

        Args:
            other (:obj:`Archive`): other archive

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.master_file == other.master_file \
            and sorted(self.files, key=ArchiveFile.sort_key) == sorted(other.files, key=ArchiveFile.sort_key) \
            and self.description == other.description \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.created == other.created \
            and self.updated == other.updated


class ArchiveFile(object):
    """ A file in an archive

    Attributes:
        filename (:obj:`str`): path to file within archive (e.g., `./models/model.xml`)
        format (:obj:`ModelFormat` or :obj:`SimFormat`): model or simulation format
        description (:obj:`str`): description
        authors (:obj:`list` of :obj:`Person`): authors of the file
        created (:obj:`datetime.datetime`): date file was created
        updated (:obj:`datetime.datetime`): date file was last updated
    """

    def __init__(self, filename=None, format=None, description=None, authors=None, created=None, updated=None):
        """
        Args:
            filename (:obj:`str`, optional): path to file within archive (e.g., `./models/model.xml`)
            format (:obj:`ModelFormat` or :obj:`SimFormat`, optional): model or simulation format
            description (:obj:`str`, optional): description
            authors (:obj:`list` of :obj:`Person`, optional): authors of the archive
            created (:obj:`datetime.datetime`, optional): date archive was created
            updated (:obj:`datetime.datetime`, optional): date archive was last updated
        """
        self.filename = filename
        self.format = format
        self.description = description
        self.authors = authors or []
        self.created = created
        self.updated = updated or created

    def __eq__(self, other):
        """ Determine if two archive files are semantically equal

        Args:
            other (:obj:`ArchiveFile`): other archive file

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.filename == other.filename \
            and self.format == other.format \
            and self.description == other.description \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.created == other.created \
            and self.updated == other.updated

    @staticmethod
    def sort_key(file):
        """ Get a key to sort a file

        Args:
            file (:obj:`ArchiveFile`): file

        Returns:
            :obj:`tuple`
        """
        return (
            file.filename,
            file.format.name if file.format else None,
            file.description,
            tuple(sorted((Person.sort_key(author) for author in file.authors))),
            file.created,
            file.updated,
        )
