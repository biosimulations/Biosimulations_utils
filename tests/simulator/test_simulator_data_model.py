""" Tests of data model for simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.archive.data_model import ArchiveFormat
from Biosimulations_utils.data_model import JournalCitation, License, OntologyTerm, Person, ResourceMetadata, Type
from Biosimulations_utils.biomodel.data_model import BiomodelingFramework, BiomodelFormat
from Biosimulations_utils.simulation.data_model import Algorithm, AlgorithmParameter, SimulationFormat
from Biosimulations_utils.simulator.data_model import Simulator
import datetime
import dateutil.tz
import unittest


class SimulatorDataModelTestCase(unittest.TestCase):
    def test_Simulator(self):
        now = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        simulator = Simulator(
            id='tellurium',
            version='2.4.1',
            url='http://tellurium.analogmachine.org/',
            docker_hub_image_id='crbm/biosimulations_tellurium:2.4.1',
            algorithms=[
                Algorithm(
                    id='00001',
                    name='integrator',
                    kisao_term=OntologyTerm(ontology='KISAO', id='00001'),
                    ontology_terms=[
                        OntologyTerm(ontology='KISAO', id='00002'),
                        OntologyTerm(ontology='KISAO', id='00003'),
                    ],
                    modeling_frameworks=[
                        BiomodelingFramework.logical.value,
                        BiomodelingFramework.flux_balance.value,
                    ],
                    model_formats=[
                        BiomodelFormat.sbml.value,
                    ],
                    simulation_formats=[
                        SimulationFormat.sedml.value,
                    ],
                    archive_formats=[
                        ArchiveFormat.combine.value,
                    ],
                    parameters=[
                        AlgorithmParameter(id='param_1',
                                           name='param 1',
                                           type=Type.float,
                                           value=1.2,
                                           recommended_range=[0.12, 12.],
                                           kisao_term=OntologyTerm(ontology='KISAO', id='00001')),
                    ],
                    citations=[
                        JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                        volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
                    ],
                )
            ],
            metadata=ResourceMetadata(
                name='tellurium',
                description='description of tellurium',
                authors=[
                    Person(first_name='John', middle_name='C', last_name='Doe'),
                    Person(first_name='Jane', middle_name='D', last_name='Doe'),
                ],
                license=License.cc0,
                created=now,
                updated=now,
            ),
        )
        self.assertEqual(Simulator.from_json(simulator.to_json()), simulator)
