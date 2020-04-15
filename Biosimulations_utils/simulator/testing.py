""" Utilities for validate containerized simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.archive import read_archive
from Biosimulations_utils.archive.data_model import ArchiveFormat
from Biosimulations_utils.archive.exec import gen_archive_for_sim
from Biosimulations_utils.data_model import JournalReference, License, OntologyTerm, Person
from Biosimulations_utils.biomodel import read_biomodel
from Biosimulations_utils.biomodel.data_model import BiomodelingFramework, BiomodelFormat, BiomodelParameter
from Biosimulations_utils.simulation import read_simulation
from Biosimulations_utils.simulation.data_model import (
    TimecourseSimulation, Algorithm, AlgorithmParameter, ParameterChange, SimulationFormat)
from Biosimulations_utils.simulator.data_model import Simulator
import copy
import datetime
import dateutil.tz
import docker
import enum
import json
import os
import numpy.testing
import pandas
import pkg_resources
import shutil
import tempfile

__all__ = ['TestCaseType', 'TestCase', 'TestCaseException', 'SimulatorValidator']


class TestCaseType(int, enum.Enum):
    """ Type of test case """
    archive = 1
    biomodel = 2


class TestCase(object):
    """ An example archive to validate simulators

    Attributes:
        filename (:obj:`str`): path to archive
        type (:obj:`TestCaseType`): type of test case
        modeling_framework (:obj:`BiomodelingFramework`): modeling framework
        model_format (:obj:`BiomodelFormat`): model format
        simulation_format (:obj:`SimulationFormat`): simulation format
        archive_format (:obj:`ArchiveFormat`): archive format
    """

    def __init__(self, filename, type, modeling_framework, model_format, simulation_format, archive_format):
        """
        Args:
            filename (:obj:`str`): path to archive
            type (:obj:`TestCaseType`): type of test case
            modeling_framework (:obj:`BiomodelingFramework`): modeling framework
            model_format (:obj:`BiomodelFormat`): model format
            simulation_format (:obj:`SimulationFormat`): simulation format
            archive_format (:obj:`ArchiveFormat`): archive format
        """
        self.filename = filename
        self.type = type
        self.modeling_framework = modeling_framework
        self.model_format = model_format
        self.simulation_format = simulation_format
        self.archive_format = archive_format

    @staticmethod
    def get_full_filename(filename):
        """ Get the full path to the file

        Returns:
            :obj:`str`: full path to the file
        """
        return pkg_resources.resource_filename('Biosimulations_utils',
                                               os.path.join('simulator', 'test-cases', filename))


class TestCaseException(object):
    """ An exception of a test case

    Attributes:
        test_case (:obj:`TestCase`): test case
        exception (:obj:`Exception`): exception
    """

    def __init__(self, test_case, exception):
        """
        Args:
            test_case (:obj:`TestCase`): test case
            exception (:obj:`Exception`): exception
        """
        self.test_case = test_case
        self.exception = exception


class SimulatorValidator(object):
    """ Validate that a Docker image for a simulator implements the BioSimulations simulator interface by
    checking that the image produces the correct outputs for one of more test cases (e.g., COMBINE archive)

    Attributes:
        _docker_client (:obj:`docker.client.DockerClient`): Docker client
    """

    # TODO: add more test cases and more detailed assertions; potentially use SBML test suite

    TEST_CASES = (
        TestCase(
            filename='BIOMD0000000297.xml',
            type=TestCaseType.biomodel,
            modeling_framework=BiomodelingFramework.non_spatial_continuous,
            model_format=BiomodelFormat.sbml,
            simulation_format=SimulationFormat.sedml,
            archive_format=ArchiveFormat.combine,
        ),
        TestCase(
            filename='BIOMD0000000297.omex',
            type=TestCaseType.archive,
            modeling_framework=BiomodelingFramework.non_spatial_continuous,
            model_format=BiomodelFormat.sbml,
            simulation_format=SimulationFormat.sedml,
            archive_format=ArchiveFormat.combine,
        ),
        TestCase(
            filename='test-bngl.omex',
            type=TestCaseType.archive,
            modeling_framework=BiomodelingFramework.non_spatial_discrete,
            model_format=BiomodelFormat.bngl,
            simulation_format=SimulationFormat.sedml,
            archive_format=ArchiveFormat.combine,
        ),
    )

    def __init__(self):
        self._docker_client = docker.from_env()

    def run(self, dockerhub_id, properties_filename):
        """ Validate that a Docker image for a simulator implements the BioSimulations simulator interface by
        checking that the image produces the correct outputs for test cases (e.g., COMBINE archive)

        Args:
            dockerhub_id (:obj:`str`): DockerHub id of simulator
            properties_filename (:obj:`str`): path to the properties of the simulator

        Returns:
            :obj:`list` :obj:`TestCase`: valid test cases
            :obj:`list` :obj:`TestCaseException`: invalid test cases
        """
        with open(properties_filename, 'r') as file:
            simulator = Simulator.from_json(json.load(file))

        valid_test_cases = []
        test_case_exceptions = []
        for test_case in self.TEST_CASES:
            for algorithm in simulator.algorithms:
                case_supports_modeling_framework = False
                for modeling_framework in algorithm.modeling_frameworks:
                    if modeling_framework.ontology == test_case.modeling_framework.value.ontology and \
                       modeling_framework.id == test_case.modeling_framework.value.id:
                        case_supports_modeling_framework = True
                        break

                case_supports_model_format = False
                for model_format in algorithm.model_formats:
                    if model_format.id == test_case.model_format.value.id:
                        case_supports_model_format = True
                        break

                case_supports_simulation_format = False
                for simulation_format in algorithm.simulation_formats:
                    if simulation_format.id == test_case.simulation_format.value.id:
                        case_supports_simulation_format = True
                        break

                case_supports_archive_format = False
                for archive_format in algorithm.archive_formats:
                    if archive_format.id == test_case.archive_format.value.id:
                        case_supports_archive_format = True
                        break

            use_test_case = case_supports_modeling_framework \
                and case_supports_model_format \
                and case_supports_simulation_format \
                and case_supports_archive_format

            if use_test_case:
                if test_case.type == TestCaseType.biomodel:
                    model_filename = test_case.get_full_filename(test_case.filename)
                    model = self._gen_example_model(model_filename)
                    simulation = self._gen_example_simulation(model)
                    simulation.model_parameter_changes = [
                        ParameterChange(parameter=BiomodelParameter(target=param.target), value=0.)
                        for param in model.parameters if param.group == 'Initial species amounts/concentrations'
                    ]
                    _, archive_filename = self._gen_example_archive(model_filename, simulation)
                else:
                    archive_filename = test_case.get_full_filename(test_case.filename)

                try:
                    self._validate_test_case(test_case, archive_filename, dockerhub_id)
                    valid_test_cases.append(test_case)
                except Exception as exception:
                    test_case_exceptions.append(TestCaseException(test_case, exception))

        print('{} passed {} test cases:\n  {}'.format(dockerhub_id, len(valid_test_cases), '\n  '.join(
            case.filename for case in valid_test_cases)))
        print('{} failed {} test cases:\n  {}'.format(dockerhub_id, len(test_case_exceptions), '\n  '.join(
            '{}\n    {}'.format(test_case_exception.test_case.filename, str(test_case_exception.exception))
            for test_case_exception in test_case_exceptions)))
        return valid_test_cases, test_case_exceptions

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

    def _validate_test_case(self, test_case, archive_filename, dockerhub_id):
        """ Validate that a simulator correctly produces the outputs for a test case

        Args:
            test_case (:obj:`TestCase`): test case
            archive_filename (:obj:`str`): path to archive
            dockerhub_id (:obj:`str`): DockerHub id of simulator
        """

        # execute archive
        out_dir = self._exec_archive(archive_filename, dockerhub_id)

        # check output
        self._assert_archive_output_valid(test_case, archive_filename, out_dir)

        # cleanup
        shutil.rmtree(out_dir)

    def _exec_archive(self, archive_filename, dockerhub_id):
        """ Execute the tasks described in a archive

        Args:
            archive_filename (:obj:`str`): path to archive
            dockerhub_id (:obj:`str`): DockerHub id of simulator

        Returns:
            :obj:`str`: directory where simulation results where saved

        Raises:
            :obj:`RuntimeError`: if the execution failed
        """
        out_dir = tempfile.mkdtemp()

        container = self._docker_client.containers.run(
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

        return out_dir

    def _assert_archive_output_valid(self, test_case, archive_filename, out_dir):
        """ Validate that the outputs of an archive were correctly generated

        Args:
            test_case (:obj:`TestCase`): test case
            archive_filename (:obj:`str`): path to archive
            out_dir (:obj:`str`): directory which contains the simulation results

        Raises:
            :obj:`AssertionError`: simulator did not generate the specified outputs
        """
        # read archive and unpack to temporary directory
        archive_dir = tempfile.mkdtemp()
        archive = read_archive(archive_filename, archive_dir)

        # validate that outputs were created
        for file in archive.files:
            if file.format.spec_url == test_case.simulation_format.value.spec_url:
                simulation_file_name = os.path.join(archive_dir, file.filename)
                simulations, _ = read_simulation(simulation_file_name)
                for simulation in simulations:
                    simulation_out_dir = os.path.join(out_dir, os.path.splitext(file.filename)[0])
                    simulation_report_filename = os.path.join(simulation_out_dir, simulation.id + '.csv')
                    assert os.path.isdir(simulation_out_dir), "Output directory {} was not created".format(simulation_out_dir)
                    assert os.path.isfile(simulation_report_filename), "Report {} was not created".format(simulation_report_filename)

                    results_data_frame = pandas.read_csv(simulation_report_filename)

                    numpy.testing.assert_array_almost_equal(
                        results_data_frame['time'],
                        numpy.linspace(simulation.output_start_time, simulation.end_time, simulation.num_time_points + 1),
                    )

                    assert set(results_data_frame.columns.to_list()) == set([var.id for var in simulation.model.variables] + ['time'])

        # cleanup
        shutil.rmtree(archive_dir)
