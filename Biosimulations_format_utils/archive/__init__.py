""" Module for representing, reading, and writing archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import ArchiveFormat, Archive  # noqa: F401
from .omex import OmexArchiveWriter, OmexArchiveReader

__all__ = ['write_archive', 'read_archive']


def write_archive(archive, in_dir, out_file, format=ArchiveFormat.omex):
    """ Write an archive

    Args:
        archive (:obj:`Archive`): description of archive
        in_dir (:obj:`str`): directory which contains the files in the archive
        out_file (:obj:`str`): path to save archive
        format (:obj:`ArchiveFormat`, optional): archive format
    """
    if format == ArchiveFormat.omex:
        Writer = OmexArchiveWriter
    else:
        raise NotImplementedError("Format {} is not supported".format(format.name))
    Writer().run(archive, in_dir, out_file)


def read_archive(in_file, out_dir, format=ArchiveFormat.omex):
    """ Read an archive

    Args:
        in_dir (:obj:`str`): directory which contains the files in the archive
        out_file (:obj:`str`): path to save archive
        format (:obj:`ArchiveFormat`, optional): archive format

    Returns:
        obj:`Archive`: description of archive
    """
    if format == ArchiveFormat.omex:
        Reader = OmexArchiveReader
    else:
        raise NotImplementedError("Format {} is not supported".format(format.name))
    return Reader().run(in_file, out_dir)
