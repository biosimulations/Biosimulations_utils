""" Utilities for generating COMBINE archives for simulations and
executing simulations in archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-10
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from . import write_archive, read_archive
from .data_model import Archive, ArchiveFile, ArchiveFormat
from ..simulation import read_simulation, write_simulation
from ..simulation.data_model import Simulation, SimulationFormat  # noqa: F401
import datetime
import dateutil.tz
import os
import tempfile
import shutil
import types  # noqa: F401

__all__ = ['gen_archive_for_sim', 'exec_simulations_in_archive']


def gen_archive_for_sim(model_filename, simulation, archive_filename, simulation_format_opts=None):
    """ Create a COMBINE archive of a simulation

    Args:
        model_filename (:obj:`str`): local path to model
        simulation (:obj:`Simulation`): simulation
        archive_filename (:obj:`str`): path to save the archive
        simulation_format_opts (:obj:`dict`, optional): keyword arguments for :obj:`write_simulation`

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
    write_simulation(simulation, os.path.join(tmp_dir, sim_archive_filename), **(simulation_format_opts or {}))

    # create archive
    archive = Archive(
        files=[
            ArchiveFile(filename='./' + model_archive_filename,
                        format=model.format,
                        description=_get_omex_description(model),
                        authors=model.authors,
                        created=model.created,
                        updated=model.updated,
                        ),
            ArchiveFile(filename='./' + sim_archive_filename,
                        format=simulation.format,
                        description=_get_omex_description(simulation),
                        authors=simulation.authors,
                        created=simulation.created,
                        updated=simulation.updated,
                        ),
        ],
        description=_get_omex_description(simulation),
        authors=simulation.authors,
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
    if obj.name:
        desc += ': ' + obj.name
    if obj.description:
        desc += '\n\n' + obj.description
    return desc


def exec_simulations_in_archive(archive_filename, task_executer, out_dir, archive_format=ArchiveFormat.combine):
    """ Execute the SED tasks represented by an archive

    Args:
        archive_filename (:obj:`str`): path to COMBINE archive
        task_executer (:obj:`types.FunctionType`): Function to execute each SED task in the archive.
            The function must implement the following interface::

                def task_executer(model_filename, model_sed_urn, simulation, working_dir, out_filename, out_format):
                    ''' Execute a simulation and save its results

                    Args:
                       model_filename (:obj:`str`): path to the model
                       model_sed_urn (:obj:`str`): SED URN for the format of the model (e.g., `urn:sedml:language:sbml`)
                       simulation (:obj:`Simulation`): simulation
                       working_dir (:obj:`str`): directory of the SED-ML file
                       out_filename (:obj:`str`): path to save the results of the simulation
                       out_format (:obj:`str`): format to save the results of the simulation (e.g., `csv`)
                    '''
                    pass

        out_dir (:obj:`str`): Directory to store the results of the tasks
        archive_format (:obj:`ArchiveFormat`, optional): archive format
    """
    # create temporary directory to unpack archive
    archive_tmp_dir = tempfile.mkdtemp()

    # unpack archive and read metadata
    archive = read_archive(archive_filename, archive_tmp_dir, format=archive_format)

    # execute simulations in archive and save results
    sim_spec_url_to_format = {format.value.spec_url: format for format in SimulationFormat.__members__.values()}
    for file in archive.files:
        # find simulation files (e.g., SED-ML files) in archive
        format = sim_spec_url_to_format.get(file.format.spec_url, None)
        if not format:
            continue

        # extract simulations (e.g., SED tasks) from file
        simulations, _ = read_simulation(os.path.join(archive_tmp_dir, file.filename), format=format)

        # create directory for outputs of simulations
        if simulations:
            out_subdir = os.path.join(out_dir, os.path.splitext(file.filename)[0])
            os.makedirs(out_subdir)

        # execute simulations
        working_dir = os.path.join(archive_tmp_dir, os.path.dirname(file.filename))
        for simulation in simulations:
            model = simulation.model
            out_filename = os.path.join(out_subdir, simulation.id + '.csv')
            task_executer(os.path.join(working_dir, model.file.name), model.format.sed_urn, simulation, working_dir, out_filename, 'csv')

    shutil.rmtree(archive_tmp_dir)
