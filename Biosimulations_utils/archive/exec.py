""" Utilities for generating COMBINE archives for simulations and
executing simulations in archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-10
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from . import write_archive
from .data_model import Archive, ArchiveFile, ArchiveFormat
from ..simulation import write_simulation
from ..simulation.data_model import Simulation  # noqa: F401
from ..visualization.data_model import Visualization  # noqa: F401
import datetime
import dateutil.tz
try:
    import docker
except ModuleNotFoundError:
    pass
import os
import tempfile
import shutil

__all__ = ['gen_archive_for_sim', 'exec_archive']


def gen_archive_for_sim(model_filename, simulation, archive_filename, simulation_format_opts=None, visualization=None):
    """ Create a COMBINE archive of a simulation

    Args:
        model_filename (:obj:`str`): local path to model
        simulation (:obj:`Simulation`): simulation
        archive_filename (:obj:`str`): path to save the archive
        simulation_format_opts (:obj:`dict`, optional): keyword arguments for :obj:`write_simulation`
        visualization (:obj:`Visualization`): visualization

    Returns:
        :obj:`Archive`: archive
    """
    # get reference to model
    model = simulation.model

    # create temporary directory for the contents of the archive
    tmp_dir = tempfile.mkdtemp()

    # copy model to the temporary directory
    model_archive_filename = '{}.{}'.format(os.path.splitext(model.file.name)[0], model.format.extension)
    shutil.copyfile(model_filename, os.path.join(tmp_dir, model_archive_filename))

    # save simulation to the temporary directory
    sim_archive_filename = '{}.{}'.format(simulation.id, simulation.format.extension)
    write_simulation(simulation, os.path.join(tmp_dir, sim_archive_filename),
                     visualization=visualization, **(simulation_format_opts or {}))

    # create archive
    archive = Archive(
        files=[
            ArchiveFile(filename='./' + model_archive_filename,
                        format=model.format,
                        description=_get_omex_description(model),
                        authors=model.metadata.authors,
                        created=model.metadata.created,
                        updated=model.metadata.updated,
                        ),
            ArchiveFile(filename='./' + sim_archive_filename,
                        format=simulation.format,
                        description=_get_omex_description(simulation),
                        authors=simulation.metadata.authors,
                        created=simulation.metadata.created,
                        updated=simulation.metadata.updated,
                        ),
        ],
        description=_get_omex_description(simulation),
        authors=simulation.metadata.authors,
    )
    archive.master_file = archive.files[1]
    archive.created = archive.updated = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)

    # save archive to a file
    write_archive(archive, tmp_dir, archive_filename, format=ArchiveFormat.combine)

    # remove temporary directory
    shutil.rmtree(tmp_dir)

    # return archive
    return archive


def _get_omex_description(obj):
    """ Encode the id, name, and description of a model or simulation into an OMEX description

    Args:
        obj (:obj:`Biomodel` or :obj:`Simulation`): object

    Returns:
        :obj:`str`: description
    """
    desc = obj.id
    if obj.metadata.name:
        desc += ': ' + obj.metadata.name
    if obj.metadata.description:
        desc += '\n\n' + obj.metadata.description
    return desc


def exec_archive(archive_filename, dockerhub_id, out_dir):
    """ Execute the tasks described in a archive

    Args:
        archive_filename (:obj:`str`): path to archive
        dockerhub_id (:obj:`str`): DockerHub id of simulator
        out_dir (:obj:`str`): directory where simulation results where saved

    Raises:
        :obj:`RuntimeError`: if the execution failed
    """
    docker_client = docker.from_env()

    container = docker_client.containers.run(
        dockerhub_id,
        volumes={
            os.path.dirname(archive_filename): {
                'bind': '/root/in',
                'mode': 'ro',
            },
            out_dir: {
                'bind': '/root/out',
                'mode': 'rw',
            }
        },
        command=['-i', '/root/in/' + os.path.basename(archive_filename), '-o', '/root/out'],
        tty=True,
        detach=True)
    status = container.wait()
    if status['StatusCode'] != 0:
        raise RuntimeError(container.logs().decode().replace('\\r\\n', '\n').strip())
    container.stop()
    container.remove()
