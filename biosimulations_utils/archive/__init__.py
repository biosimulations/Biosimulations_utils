""" Module for representing, reading, and writing archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import ArchiveFormat, Archive  # noqa: F401
from .combine import CombineArchiveWriter, CombineArchiveReader

__all__ = ['write_archive', 'read_archive']


def write_archive(archive, in_dir, out_file, format=ArchiveFormat.combine):
    """ Write an archive

    Args:
        archive (:obj:`Archive`): description of archive
        in_dir (:obj:`str`): directory which contains the files in the archive
        out_file (:obj:`str`): path to save archive
        format (:obj:`ArchiveFormat`, optional): archive format

    Raises:
        :obj:`NotImplementedError`: the format is not supported
    """
    if format == ArchiveFormat.combine:
        Writer = CombineArchiveWriter
    else:
        raise NotImplementedError("Format {} is not supported".format(format.name))
    Writer().run(archive, in_dir, out_file)


def read_archive(in_file, out_dir, format=ArchiveFormat.combine):
    """ Read an archive

    Args:
        in_dir (:obj:`str`): directory which contains the files in the archive
        out_file (:obj:`str`): path to save archive
        format (:obj:`ArchiveFormat`, optional): archive format

    Returns:
        :obj:`Archive`: description of archive

    Raises:
        :obj:`NotImplementedError`: the format is not supported
    """
    if format == ArchiveFormat.combine:
        Reader = CombineArchiveReader
    else:
        raise NotImplementedError("Format {} is not supported".format(format.name))
    return Reader().run(in_file, out_dir)
