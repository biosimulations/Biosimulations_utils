""" Base clases for reading and writing archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Archive  # noqa: F401
import abc


__all__ = ['ArchiveWriter', 'ArchiveReader', 'ArchiveIoError', 'ArchiveIoWarning']


class ArchiveWriter(abc.ABC):
    """ Writer for archives """
    @abc.abstractmethod
    def run(archive, in_dir, out_file):
        """ Write an archive to a file

        Args:
            archive (:obj:`Archive`): description of archive
            in_dir (:obj:`str`): directory which contains the files in the archive
            out_file (:obj:`str`): path to save archive
        """
        pass  # pragma: no cover


class ArchiveReader(abc.ABC):
    """ Reader for COMBINE/OMEX archives """

    @abc.abstractmethod
    def run(in_file, out_dir):
        """ Read an archive from a file

        Args:
            in_file (:obj:`str`): path to save archive
            out_dir (:obj:`str`): directory which contains the files in the archive

        Returns:
            :obj:`Archive`: description of archive
        """
        pass  # pragma: no cover


class ArchiveIoError(Exception):
    """ Archive IO error """
    pass


class ArchiveIoWarning(UserWarning):
    """ Archive IO warning """
    pass
