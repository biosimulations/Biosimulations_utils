""" Data model for simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, Identifier, JournalReference, License, OntologyTerm, Person, RemoteFile, Type
from ..biomodel.data_model import Biomodel, BiomodelParameter, BiomodelVariable
import wc_utils.util.enumerate

__all__ = [
    'SimulationFormat',
    'Simulation', 'TimecourseSimulation', 'SteadyStateSimulation',
    'Simulator', 'Algorithm', 'AlgorithmParameter', 'ParameterChange',
    'SimulationResult',
]


class SimulationFormat(wc_utils.util.enumerate.CaseInsensitiveEnum):
    """ Simulation format metadata """
    SEDML = Format(
        id='SEDML',
        name='Simulation Experiment Description Markup Language',
        edam_id='format_3685',
        url='https://sed-ml.org/',
        spec_url='http://identifiers.org/combine.specifications/sed-ml',
    )

    SESSL = Format(
        id='SESSL',
        name='Simulation Experiment Specification via a Scala Layer',
        edam_id=None,
        url='http://sessl.org',
        spec_url='http://sessl.org',
    )


class Simulation(object):
    """ Simulation experiments

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        image (:obj:`RemoteFile`): image file
        description (:obj:`str`): description
        tags (:obj:`list` of :obj:`str`): tags
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        references (:obj:`list` of :obj:`JournalReference`): references
        authors (:obj:`list` of :obj:`Person`): authors
        license (:obj:`License`): license
        format (:obj:`Format`): format
        model (:obj:`Biomodel`): model
        model_parameter_changes (:obj:`list` of :obj:`ParameterChange`): model parameter changes
        algorithm (:obj:`Algorithm`): simulation algorithm
        algorithm_parameter_changes (:obj:`list` of :obj:`ParameterChange`): simulation algorithm parameter changes
    """

    def __init__(self, id=None, name=None, image=None, description=None,
                 tags=None, identifiers=None, references=None, authors=None, license=None, format=None,
                 model=None, model_parameter_changes=None,
                 algorithm=None, algorithm_parameter_changes=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            image (:obj:`RemoteFile`, optional): image file
            description (:obj:`str`, optional): description
            tags (:obj:`list` of :obj:`str`, optional): tags
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            references (:obj:`list` of :obj:`JournalReference`, optional): references
            authors (:obj:`list` of :obj:`Person`, optional): authors
            license (:obj:`License`, optional): license
            format (:obj:`Format`, optional): format
            model (:obj:`Biomodel`, optional): model
            model_parameter_changes (:obj:`list` of :obj:`ParameterChange`, optional): model parameter changes
            algorithm (:obj:`Algorithm`, optional): simulation algorithm
            algorithm_parameter_changes (:obj:`list` of :obj:`ParameterChange`, optional): simulation algorithm parameter changes
        """
        self.id = id
        self.name = name
        self.image = image
        self.description = description
        self.tags = tags or []
        self.identifiers = identifiers or []
        self.references = references or []
        self.authors = authors or []
        self.license = license
        self.format = format
        self.model = model
        self.model_parameter_changes = model_parameter_changes or []
        self.algorithm = algorithm
        self.algorithm_parameter_changes = algorithm_parameter_changes or []

    def __eq__(self, other):
        """ Determine if two simulations are semantically equal

        Args:
            other (:obj:`Simulation`): other simulation

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and self.image == other.image \
            and self.description == other.description \
            and sorted(self.tags) == sorted(other.tags) \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and sorted(self.references, key=JournalReference.sort_key) == sorted(other.references, key=JournalReference.sort_key) \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.license == other.license \
            and self.format == other.format \
            and self.model == other.model \
            and sorted(self.model_parameter_changes, key=ParameterChange.sort_key) == \
            sorted(other.model_parameter_changes, key=ParameterChange.sort_key) \
            and self.algorithm == other.algorithm \
            and sorted(self.algorithm_parameter_changes, key=ParameterChange.sort_key) == \
            sorted(other.algorithm_parameter_changes, key=ParameterChange.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
            'image': self.image.to_json() if self.image else None,
            'description': self.description,
            'tags': self.tags or [],
            'identifiers': [identifier.to_json() for identifier in self.identifiers],
            'references': [ref.to_json() for ref in self.references],
            'authors': [author.to_json() for author in self.authors],
            'license': self.license.value if self.license else None,
            'format': self.format.to_json() if self.format else None,
            'model': self.model.to_json() if self.model else None,
            'modelParameterChanges': [change.to_json() for change in self.model_parameter_changes],
            'algorithm': self.algorithm.to_json() if self.algorithm else None,
            'algorithmParameterChanges': [change.to_json() for change in self.algorithm_parameter_changes],
        }

    @classmethod
    def from_json(cls, val):
        """ Create simulation from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Simulation`
        """
        if cls == Simulation:
            if 'startTime' in val or 'endTime' in val or 'numTimePoints' in val:
                subcls = TimecourseSimulation
            else:
                subcls = SteadyStateSimulation
            return subcls.from_json(val)

        else:
            return cls(
                id=val.get('id', None),
                name=val.get('name', None),
                image=RemoteFile.from_json(val.get('image')) if val.get('image', None) else None,
                description=val.get('description', None),
                tags=val.get('tags', []),
                identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
                references=[JournalReference.from_json(ref) for ref in val.get('references', [])],
                authors=[Person.from_json(author) for author in val.get('authors', [])],
                license=License(val.get('license')) if val.get('license', None) else None,
                format=Format.from_json(val.get('format')) if val.get('format', None) else None,
                model=Biomodel.from_json(val.get('model')) if val.get('model', None) else None,
                model_parameter_changes=[ParameterChange.from_json(change, BiomodelParameter)
                                         for change in val.get('modelParameterChanges', [])],
                algorithm=Algorithm.from_json(val.get('algorithm')) if val.get('algorithm', None) else None,
                algorithm_parameter_changes=[ParameterChange.from_json(change, AlgorithmParameter)
                                             for change in val.get('algorithmParameterChanges', [])]
            )


class TimecourseSimulation(Simulation):
    """ Timecourse simulation

    Attributes:
        start_time (:obj:`float`): start time
        output_start_time (:obj:`float`): time to begin recording simulation results
        end_time (:obj:`float`): end time
        num_time_points (:obj:`int`): number of time points to record
    """

    def __init__(self, id=None, name=None, image=None, description=None,
                 tags=None, identifiers=None, references=None, authors=None, license=None, format=None,
                 model=None, model_parameter_changes=None,
                 start_time=None, output_start_time=None, end_time=None, num_time_points=None,
                 algorithm=None, algorithm_parameter_changes=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            image (:obj:`RemoteFile`, optional): image file
            description (:obj:`str`, optional): description
            tags (:obj:`list` of :obj:`str`, optional): tags
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            references (:obj:`list` of :obj:`JournalReference`, optional): references
            authors (:obj:`list` of :obj:`Person`, optional): authors
            license (:obj:`License`, optional): license
            format (:obj:`Format`, optional): format
            model (:obj:`Biomodel`, optional): model
            model_parameter_changes (:obj:`list` of :obj:`ParameterChange`, optional): model parameter changes
            start_time (:obj:`float`, optional): start time
            output_start_time (:obj:`float`, start): time to begin recording simulation results
            end_time (:obj:`float`, optional): end time
            num_time_points (:obj:`int`, optional): number of time points to record
            algorithm (:obj:`Algorithm`, optional): simulation algorithm
            algorithm_parameter_changes (:obj:`list` of :obj:`ParameterChange`, optional): simulation algorithm parameter changes
        """
        super(TimecourseSimulation, self).__init__(id=id, name=name, image=image, description=description,
                                                   tags=tags, identifiers=identifiers,
                                                   references=references, authors=authors, license=license, format=format,
                                                   model=model, model_parameter_changes=model_parameter_changes,
                                                   algorithm=algorithm, algorithm_parameter_changes=algorithm_parameter_changes)
        self.start_time = start_time
        self.output_start_time = output_start_time
        self.end_time = end_time
        self.num_time_points = num_time_points

    def __eq__(self, other):
        """ Determine if two simulations are semantically equal

        Args:
            other (:obj:`TimecourseSimulation`): other algorithm

        Returns:
            :obj:`bool`
        """
        return super(TimecourseSimulation, self).__eq__(other) \
            and self.start_time == other.start_time \
            and self.output_start_time == other.output_start_time \
            and self.end_time == other.end_time \
            and self.num_time_points == other.num_time_points

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        val = super(TimecourseSimulation, self).to_json()
        val['startTime'] = self.start_time
        val['outputStartTime'] = self.output_start_time
        val['endTime'] = self.end_time
        val['numTimePoints'] = self.num_time_points
        return val

    @classmethod
    def from_json(cls, val):
        """ Create simulation from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`TimecourseSimulation`
        """
        obj = super(TimecourseSimulation, cls).from_json(val)
        obj.start_time = val.get('startTime', None)
        obj.output_start_time = val.get('outputStartTime', None)
        obj.end_time = val.get('endTime', None)
        obj.num_time_points = val.get('numTimePoints', None)
        return obj


class SteadyStateSimulation(Simulation):
    """ Steady-state simulation """
    pass


class Simulator(object):
    """ A simulator

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        version (:obj:`str`): version
        image (:obj:`RemoteFile`): image file
        description  (:obj:`str`): description
        url (:obj:`str`): URL
        tags (:obj:`list` of :obj:`str`): tags
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        references (:obj:`list` of :obj:`JournalReference`): references
        authors (:obj:`list` of :obj:`Person`): authors
        license (:obj:`License`): license
        format (:obj:`Format`): format
        docker_hub_image_id (:obj:`str`): id for image in DockerHub (e.g., "crbm/biosimulatons_tellurium:2.4.1")
        algorithms (:obj:`list` of :obj:`Algorithm`): supported algorithms
    """

    def __init__(self, id=None, name=None, version=None, image=None, description=None, url=None,
                 tags=None, identifiers=None, references=None, authors=None, license=None,
                 format=None, docker_hub_image_id=None, algorithms=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            version (:obj:`str`, optional): version
            image (:obj:`RemoteFile`, optional): image file
            description  (:obj:`str`, optional): description
            url (:obj:`str`, optional): URL
            tags (:obj:`list` of :obj:`str`, optional): tags
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            references (:obj:`list` of :obj:`JournalReference`, optional): references
            authors (:obj:`list` of :obj:`Person`, optional): authors
            license (:obj:`License`, optional): license
            format (:obj:`Format`, optional): format
            docker_hub_image_id (:obj:`str`, optional): id for image in DockerHub (e.g., "crbm/biosimulatons_tellurium:2.4.1")
            algorithms (:obj:`list` of :obj:`Algorithm`, optional): supported algorithms
        """
        self.id = id
        self.name = name
        self.version = version
        self.image = image
        self.description = description
        self.url = url
        self.tags = tags or []
        self.identifiers = identifiers or []
        self.references = references or []
        self.authors = authors or []
        self.license = license
        self.format = format
        self.docker_hub_image_id = docker_hub_image_id
        self.algorithms = algorithms or []

    def __eq__(self, other):
        """ Determine if two simulators are semantically equal

        Args:
            other (:obj:`Simulator`): other simulator

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and self.version == other.version \
            and self.image == other.image \
            and self.description == other.description \
            and self.url == other.url \
            and sorted(self.tags) == sorted(other.tags) \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and sorted(self.references, key=JournalReference.sort_key) == sorted(other.references, key=JournalReference.sort_key) \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.license == other.license \
            and self.format == other.format \
            and self.docker_hub_image_id == other.docker_hub_image_id \
            and sorted(self.algorithms, key=Algorithm.sort_key) == sorted(other.algorithms, key=Algorithm.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'image': self.image.to_json() if self.image else None,
            'description': self.description,
            'url': self.url,
            'tags': self.tags or [],
            'identifiers': [identifier.to_json() for identifier in self.identifiers],
            'references': [ref.to_json() for ref in self.references],
            'authors': [author.to_json() for author in self.authors],
            'license': self.license.value if self.license else None,
            'format': self.format.to_json() if self.format else None,
            'dockerHubImageId': self.docker_hub_image_id,
            'algorithms': [alg.to_json() for alg in self.algorithms],
        }

    @classmethod
    def from_json(cls, val):
        """ Create simulator from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Simulation`
        """
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
            version=val.get('version', None),
            image=RemoteFile.from_json(val.get('image')) if val.get('image', None) else None,
            description=val.get('description', None),
            url=val.get('url', None),
            tags=val.get('tags', []),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            references=[JournalReference.from_json(ref) for ref in val.get('references', [])],
            authors=[Person.from_json(author) for author in val.get('authors', [])],
            license=License(val.get('license')) if val.get('license', None) else None,
            format=Format.from_json(val.get('format')) if val.get('format', None) else None,
            docker_hub_image_id=val.get('dockerHubImageId', None),
            algorithms=[Algorithm.from_json(alg) for alg in val.get('algorithms', [])],
        )


class Algorithm(object):
    """ Simulation algorithm

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        kisao_term (:obj:`OntologyTerm`): KiSAO id
        ontology_terms (:obj:`list` of :obj:`OntologyTerm`): list of sematically equivalent
            KiSAO ids for the parent simulator of an algorithm
        modeling_frameworks (:obj:`list` of :obj:`OntologyTerm`): supported modeling frameworks
        model_formats (:obj:`list` of :obj:`Format`): supoorted model formats
        parameters (:obj:`list` of :obj:`AlgorithmParameter`): parameters
    """

    def __init__(self, id=None, name=None, kisao_term=None, ontology_terms=None,
                 modeling_frameworks=None, model_formats=None, parameters=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            kisao_term (:obj:`OntologyTerm`, optional): KiSAO id
            ontology_terms (:obj:`list` of :obj:`OntologyTerm`, optional): list of sematically equivalent
                KiSAO ids for the parent simulator of an algorithm
            modeling_frameworks (:obj:`list` of :obj:`OntologyTerm`, optional): supported modeling frameworks
            model_formats (:obj:`list` of :obj:`Format`, optional): supoorted model formats
            parameters (:obj:`list` of :obj:`AlgorithmParameter`, optional): parameters
        """
        self.id = id
        self.name = name
        self.kisao_term = kisao_term
        self.ontology_terms = ontology_terms or []
        self.modeling_frameworks = modeling_frameworks or []
        self.model_formats = model_formats or []
        self.parameters = parameters or []

    def __eq__(self, other):
        """ Determine if two algorithms are semantically equal

        Args:
            other (:obj:`Algorithm`): other algorithm

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and self.kisao_term == other.kisao_term \
            and sorted(self.ontology_terms, key=OntologyTerm.sort_key) == sorted(other.ontology_terms, key=OntologyTerm.sort_key) \
            and sorted(self.modeling_frameworks, key=OntologyTerm.sort_key) == \
            sorted(other.modeling_frameworks, key=OntologyTerm.sort_key) \
            and sorted(self.model_formats, key=Format.sort_key) == sorted(other.model_formats, key=Format.sort_key) \
            and sorted(self.parameters, key=AlgorithmParameter.sort_key) == sorted(other.parameters, key=AlgorithmParameter.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
            'kisaoTerm': self.kisao_term.to_json() if self.kisao_term else None,
            'ontologyTerms': [term.to_json() for term in self.ontology_terms],
            'modelingFrameworks': [framework.to_json() for framework in self.modeling_frameworks],
            'modelFormats': [format.to_json() for format in self.model_formats],
            'parameters': [param.to_json() for param in self.parameters],
        }

    @classmethod
    def from_json(cls, val):
        """ Create algorithm from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Algorithm`
        """
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
            kisao_term=OntologyTerm.from_json(val.get('kisaoTerm')) if val.get('kisaoTerm', None) else None,
            ontology_terms=[OntologyTerm.from_json(term) for term in val.get('ontologyTerms', [])],
            modeling_frameworks=[OntologyTerm.from_json(framework) for framework in val.get('modelingFrameworks', [])],
            model_formats=[Format.from_json(format) for format in val.get('modelFormats', [])],
            parameters=[AlgorithmParameter.from_json(param) for param in val.get('parameters', [])],
        )

    @staticmethod
    def sort_key(algorithm):
        """ Get a key to sort an algorithm

        Args:
            algorithm (:obj:`Algorithm`): algorithm

        Returns:
            :obj:`tuple`
        """
        return (
            algorithm.id,
            algorithm.name,
            algorithm.kisao_term.sort_key(algorithm.kisao_term),
            tuple([term.sort_key(term) for term in algorithm.ontology_terms]),
            tuple([framework.sort_key(framework) for framework in algorithm.modeling_frameworks]),
            tuple([format.sort_key(format) for format in algorithm.model_formats]),
            tuple([param.sort_key(param) for param in algorithm.parameters]),
        )


class AlgorithmParameter(object):
    """ Algorithm parameter

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        type (:obj:`Type`): type
        value (:obj:`object`): value
        recommended_range (:obj:`list` of :obj:`object`): recommend minimum and maximum values
        kisao_term (:obj:`OntologyTerm`): KiSAO term
    """

    def __init__(self, id=None, name=None, type=None, value=None, recommended_range=None, kisao_term=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            type (:obj:`Type`, optional): type
            value (:obj:`object`, optional): value
            recommended_range (:obj:`list` of :obj:`object`, optional): recommend minimum and maximum values
            kisao_term (:obj:`OntologyTerm`, optional): KiSAO term
        """
        self.id = id
        self.name = name
        self.type = type
        self.value = value
        self.recommended_range = recommended_range or []
        self.kisao_term = kisao_term

    def __eq__(self, other):
        """ Determine if two algorithm parameters are semantically equal

        Args:
            other (:obj:`AlgorithmParameter`): other algorithm parameter

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and self.type == other.type \
            and self.value == other.value \
            and self.recommended_range == other.recommended_range \
            and self.kisao_term == other.kisao_term

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value if self.type else None,
            'value': self.value,
            'recommendedRange': self.recommended_range,
            'kisaoTerm': self.kisao_term.to_json() if self.kisao_term else None,
        }

    @classmethod
    def from_json(cls, val):
        """ Create algorithm parameter from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`AlgorithmParameter`
        """
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
            type=Type(val.get('type')) if val.get('type', None) else None,
            value=val.get('value', None),
            recommended_range=val.get('recommendedRange', []),
            kisao_term=OntologyTerm.from_json(val.get('kisaoTerm')) if val.get('kisaoTerm', None) else None,
        )

    @staticmethod
    def sort_key(parameter):
        """ Get a key to sort an algorithm parameter

        Args:
            parameter (:obj:`AlgorithmParameter`): algorithm parameter

        Returns:
            :obj:`tuple`
        """
        return (
            parameter.id,
            parameter.name,
            parameter.type.value if parameter.type else None,
            parameter.value,
            tuple(parameter.recommended_range),
            parameter.kisao_term.sort_key(parameter.kisao_term),
        )


class ParameterChange(object):
    """ BiomodelParameter change

    Attributes:
        parameter (:obj:`BiomodelParameter` or :obj:`AlgorithmParameter`): parameter
        value (:obj:`object`): value
    """

    def __init__(self, parameter=None, value=None):
        """
        Args:
            parameter (:obj:`BiomodelParameter` or :obj:`AlgorithmParameter`, optional): parameter
            value (:obj:`object`, optional): value
        """
        self.parameter = parameter
        self.value = value

    def __eq__(self, other):
        """ Determine if two parameter changes are semantically equal

        Args:
            other (:obj:`ParameterChange`): other parameter change

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.parameter == other.parameter \
            and self.value == other.value

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'parameter': self.parameter.to_json() if self.parameter else None,
            'value': self.value,
        }

    @classmethod
    def from_json(cls, val, ParameterType):
        """ Create parameter change from JSON

        Args:
            val (:obj:`dict`)
            ParameterType (:obj:`type`): type of parameter

        Returns:
            :obj:`ParameterChange`
        """
        return cls(
            parameter=ParameterType.from_json(val.get('parameter')) if val.get('parameter', None) else None,
            value=val.get('value', None),
        )

    @staticmethod
    def sort_key(change):
        """ Get a key to sort a parameter change

        Args:
            change (:obj:`ParameterChange`): parameter change

        Returns:
            :obj:`tuple`
        """
        return (change.parameter.sort_key(change.parameter), change.value)


class SimulationResult(object):
    """ Simulation result

    Attributes:
        simulation (:obj:`Simulation`): simulation
        variable (:obj:`BiomodelVariable`): model variable
    """

    def __init__(self, simulation=None, variable=None):
        """
        Args:
            simulation (:obj:`Simulation`): simulation
            variable (:obj:`BiomodelVariable`): model variable
        """
        self.simulation = simulation
        self.variable = variable

    def __eq__(self, other):
        """ Determine if two simulation results are semantically equal

        Args:
            other (:obj:`SimulationResult`): other simulation result

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.simulation == other.simulation \
            and self.variable == other.variable

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'simulation': self.simulation.to_json() if self.simulation else None,
            'variable': self.variable.to_json() if self.variable else None,
        }

    @classmethod
    def from_json(cls, val):
        """ Create simulation result from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`SimulationResult`
        """
        return cls(
            simulation=Simulation.from_json(val.get('simulation')) if val.get('simulation', None) else None,
            variable=BiomodelVariable.from_json(val.get('variable')) if val.get('variable', None) else None,
        )

    @staticmethod
    def sort_key(result):
        """ Get a key to sort a simulation result

        Args:
            result (:obj:`SimulationResult`): simulation result

        Returns:
            :obj:`tuple`
        """
        return (result.simulation.id, result.variable.id)
