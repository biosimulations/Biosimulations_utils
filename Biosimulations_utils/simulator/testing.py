""" Utilities for validate containerized simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.archive.exec import gen_archive_for_sim
from Biosimulations_utils.data_model import JournalReference, License, OntologyTerm, Person
from Biosimulations_utils.biomodel import read_biomodel
from Biosimulations_utils.biomodel.data_model import BiomodelFormat, BiomodelParameter
from Biosimulations_utils.simulation.data_model import (
    TimecourseSimulation, Algorithm, AlgorithmParameter, ParameterChange, SimulationFormat)
import abc
import copy
import datetime
import dateutil.tz
import docker
import os
import numpy.testing
import pandas
import pkg_resources
import shutil
import tempfile

__all__ = ['SbmlSedmlCombineSimulatorValidator']


class SimulatorValidator(abc.ABC):
    """ Validate that a Docker image for a simulator implements the BioSimulatons simulator interface by
    checking that the image produces the correct outputs for example models

    Attributes:
        _docker_client (:obj:`docker.client.DockerClient`): Docker client
    """

    def __init__(self):
        self._docker_client = docker.from_env()

    @abc.abstractmethod
    def run(self):
        """ Validate that a Docker image for a simulator implements the BioSimulatons simulator interface by
        checking that the image produces the correct outputs for example models

        Args:
            dockerhub_id (:obj:`str`): DockerHub id of simulator
        """
        pass  # pragma: no cover


class SbmlSedmlCombineSimulatorValidator(SimulatorValidator):
    """ Validate that a Docker image for a SBML/SED-ML/COMBINE simulator implements the BioSimulatons simulator interface by
    checking that the image produces the correct outputs for example models
    """
    EXAMPLE_MODEL_FILENAMES = (
        pkg_resources.resource_filename('Biosimulations_utils', os.path.join('simulator', 'testing-examples', 'BIOMD0000000297.xml')),
    )

    def run(self, dockerhub_id):
        """ Validate that a Docker image for a simulator implements the BioSimulatons simulator interface by
        checking that the image produces the correct outputs for example models

        Args:
            dockerhub_id (:obj:`str`): DockerHub id of simulator
        """
        for model_filename in self.EXAMPLE_MODEL_FILENAMES:
            self._validate_example(model_filename, dockerhub_id)

    def _validate_example(self, model_filename, dockerhub_id):
        """ Validate that a simulator correctly produces the outputs for a simulation of a model

        Args:
            model_filename (:obj:`str`): path to example model
            dockerhub_id (:obj:`str`): DockerHub id of simulator

        Raises:
            :obj:`AssertionError`: simulator isn't correctly processing model parameter changes
        """
        # simulate without parameter changes
        model_1 = self._gen_example_model(model_filename)
        simulation_1 = self._gen_example_simulation(model_1)
        _, archive_filename_1 = self._gen_example_archive(model_filename, simulation_1)
        out_dir_1 = self._exec_archive(simulation_1, archive_filename_1, dockerhub_id)
        self._assert_archive_output_valid(model_1, simulation_1, out_dir_1)

        # simulate with parameter changes
        model_2 = self._gen_example_model(model_filename)
        simulation_2 = self._gen_example_simulation(model_2)
        simulation_2.model_parameter_changes = [
            ParameterChange(parameter=BiomodelParameter(target=param.target), value=0.)
            for param in model_2.parameters if param.group == 'Initial species amounts/concentrations'
        ]
        _, archive_filename_2 = self._gen_example_archive(model_filename, simulation_2)
        out_dir_2 = self._exec_archive(simulation_2, archive_filename_2, dockerhub_id)
        self._assert_archive_output_valid(model_2, simulation_2, out_dir_2)

        # check that results are different
        data_frame_1 = pandas.read_csv(os.path.join(out_dir_1, simulation_1.id, simulation_1.id + '.csv'))
        data_frame_2 = pandas.read_csv(os.path.join(out_dir_2, simulation_1.id, simulation_1.id + '.csv'))
        assert (data_frame_1.to_numpy() != data_frame_2.to_numpy()).any()

        # cleanup
        os.remove(archive_filename_1)
        os.remove(archive_filename_2)
        shutil.rmtree(out_dir_1)
        shutil.rmtree(out_dir_2)

    def _gen_example_model(self, model_filename):
        """ Generate an example model

        Args:
            model_filename (:obj:`str`): path to example model

        Returns:
            :obj:`Biomodel`: example model
        """
        model = read_biomodel(model_filename, format=BiomodelFormat.sbml)
        model.file.name = 'BIOMD0000000297_url.xml'
        model.description = 'Description of model 1'
        model.tags = ['tag-model-a', 'tag-model-b', 'tag-model-c']
        model.references = [
            JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                             volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
        ]
        model.authors = [
            Person(first_name='Jack', middle_name='A', last_name='Doe'),
            Person(first_name='Jill', middle_name='B', last_name='Doe'),
        ]
        model.license = License.cc0
        model.created = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        model.updated = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        return model

    def _gen_example_simulation(self, model):
        """ Generate an example simulation

        Args:
            model (:obj:`Biomodel`): model

        Returns:
            :obj:`Simulation`: example simulation
        """
        simulation = TimecourseSimulation(
            id='simulation_1',
            name='simulation 1',
            description='Description of simulation 1',
            tags=['tag-simulation-a', 'tag-simulation-b', 'tag-simulation-c'],
            references=[
                JournalReference(authors='John Doe and Jane Doe', title='title', journal='journal',
                                 volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
            ],
            authors=[
                Person(first_name='John', middle_name='C', last_name='Doe'),
                Person(first_name='Jane', middle_name='D', last_name='Doe'),
            ],
            license=License.cc0,
            created=datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC),
            updated=datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC),
            model=model,
            model_parameter_changes=[
            ],
            start_time=0.,
            output_start_time=0.,
            end_time=10.,
            num_time_points=100,
            algorithm=Algorithm(
                kisao_term=OntologyTerm(
                    ontology='KISAO',
                    id='0000019',
                    name='CVODE',
                ),
                id='CVODE',
                name='C-language Variable-coefficient Ordinary Differential Equation solver',
            ),
            algorithm_parameter_changes=[
                ParameterChange(
                    parameter=AlgorithmParameter(
                        kisao_term=OntologyTerm(
                            ontology='KISAO',
                            id='0000209',
                        ),
                        id='rel_tol',
                        name='Relative tolerance',
                    ),
                    value=1e-5,
                ),
                ParameterChange(
                    parameter=AlgorithmParameter(
                        kisao_term=OntologyTerm(
                            ontology='KISAO',
                            id='0000211',
                        ),
                        id='abs_tol',
                        name='Absolute tolerance',
                    ),
                    value=1e-11,
                ),
            ],
            format=copy.copy(SimulationFormat.sedml.value),
        )
        simulation.format.version = 'L1V3'

        return simulation

    def _gen_example_archive(self, model_filename, simulation):
        """ Encode a simulation into SED-ML and generate an example COMBINE archive for it

        Args:
            model_filename (:obj:`str`): path to example model
            simulation (:obj:`Simulation`): simulation of model

        Returns:
            :obj:`tuple`:

                * :obj:`Archive`: properties of the archive
                * :obj:`str`: path to archive
        """
        fid, archive_filename = tempfile.mkstemp(suffix='.omex')
        os.close(fid)
        archive = gen_archive_for_sim(model_filename, simulation, archive_filename)
        return (archive, archive_filename)

    def _exec_archive(self, simulation, archive_filename, dockerhub_id):
        """ Execute the tasks described in a COMBINE archive

        Args:
            simulation (:obj:`Simulation`): simulation of model
            archive_filename (:obj:`str`): path to archive
            dockerhub_id (:obj:`str`): DockerHub id of simulator

        Returns:
            :obj:`str`: directory where simulation results where saved
        """
        out_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(out_dir, simulation.id))

        self._docker_client.containers.run(
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
            remove=True)
        return out_dir

    def _assert_archive_output_valid(self, model, simulation, out_dir):
        """ Validate that the outputs of an archive were correctly generated

        Args:
            model (:obj:`Biomodel`): model
            simulation (:obj:`Simulation`): simulation
            out_dir (:obj:`str`): directory which contains the simulation results

        Raises:
            :obj:`AssertionError`: simulator did not generate the specified outputs
        """
        assert os.listdir(out_dir) == [simulation.id]
        assert os.listdir(os.path.join(out_dir, simulation.id)) == [simulation.id + '.csv']
        data_frame = pandas.read_csv(os.path.join(out_dir, simulation.id, simulation.id + '.csv'))
        assert set(data_frame.columns.to_list()) == set([var.id for var in model.variables] + ['time'])
        numpy.testing.assert_array_almost_equal(data_frame['time'], numpy.linspace(0., 10., 101))
