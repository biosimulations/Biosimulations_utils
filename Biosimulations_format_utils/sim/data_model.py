""" Data model for simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, JournalReference, License, Person, RemoteFile, Type
from ..model.data_model import Model, Parameter
import types

__all__ = ['Simulation', 'Algorithm', 'AlgorithmParameter', 'ParameterChange']


class Simulation(object):
    """ Simulation experiments

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        image (:obj:`RemoteFile`): image file
        description (:obj:`str`): description
        tags (:obj:`list` of :obj:`str`): tags
        refs (:obj:`list` of :obj:`JournalReference`): references
        authors (:obj:`list` of :obj:`Person`): authors
        license (:obj:`License`): license
        format (:obj:`Format`): format
        model (:obj:`Model`): model
        model_parameter_changes (:obj:`list` of :obj:`ParameterChange`): model parameter changes
        start_time (:obj:`float`): start time
        end_time (:obj:`float`): end time
        length (:obj:`float`): length
        num_time_points (:obj:`int`): number of time points to record
        algorithm (:obj:`Algorithm`): simulation algorithm
        algorithm_parameter_changes (:obj:`list` of :obj:`ParameterChange`): simulation algorithm parameter changes
    """

    def __init__(self, id=None, name=None, image=None, description=None, tags=None, refs=None, authors=None, license=None, format=None,
                 model=None, model_parameter_changes=None,
                 start_time=None, end_time=None, num_time_points=None,
                 algorithm=None, algorithm_parameter_changes=None, ):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            image (:obj:`RemoteFile`, optional): image file
            description (:obj:`str`, optional): description
            tags (:obj:`list` of :obj:`str`, optional): tags
            refs (:obj:`list` of :obj:`JournalReference`, optional): references
            authors (:obj:`list` of :obj:`Person`, optional): authors
            license (:obj:`License`, optional): license
            format (:obj:`Format`, optional): format
            model (:obj:`Model`, optional): model
            model_parameter_changes (:obj:`list` of :obj:`ParameterChange`, optional): model parameter changes
            start_time (:obj:`float`, optional): start time
            end_time (:obj:`float`, optional): end time
            num_time_points (:obj:`int`, optional): number of time points to record
            algorithm (:obj:`Algorithm`, optional): simulation algorithm
            algorithm_parameter_changes (:obj:`list` of :obj:`ParameterChange`, optional): simulation algorithm parameter changes
        """
        self.id = id
        self.name = name
        self.image = image
        self.description = description
        self.tags = tags or []
        self.refs = refs or []
        self.authors = authors or []
        self.license = license
        self.format = format
        self.model = model
        self.model_parameter_changes = model_parameter_changes or []
        self.start_time = start_time
        self.end_time = end_time
        self.length = end_time - start_time if start_time is not None and end_time is not None else None
        self.num_time_points = num_time_points
        self.algorithm = algorithm
        self.algorithm_parameter_changes = algorithm_parameter_changes or []

    def __eq__(self, other):
        """ Determine if two simulations are semantically equal

        Args:
            other (:obj:`Simulation`): other simulation

        Returns:
            :obj:`bool`
        """
        return isinstance(other, self.__class__) \
            and self.id == other.id \
            and self.name == other.name \
            and self.image == other.image \
            and self.description == other.description \
            and sorted(self.tags) == sorted(other.tags) \
            and sorted(self.refs, key=JournalReference.sort_key) == sorted(other.refs, key=JournalReference.sort_key) \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.license == other.license \
            and self.format == other.format \
            and self.model == other.model \
            and sorted(self.model_parameter_changes, key=ParameterChange.sort_key) == \
            sorted(other.model_parameter_changes, key=ParameterChange.sort_key) \
            and self.start_time == other.start_time \
            and self.end_time == other.end_time \
            and self.num_time_points == other.num_time_points \
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
            'refs': [ref.to_json() for ref in self.refs],
            'authors': [author.to_json() for author in self.authors],
            'license': self.license.value if self.license else None,
            'format': self.format.to_json() if self.format else None,
            'model': self.model.to_json() if self.model else None,
            'modelParameterChanges': [change.to_json() for change in self.model_parameter_changes],
            'startTime': self.start_time,
            'endTime': self.end_time,
            'length': self.length,
            'numTimePoints': self.num_time_points,
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
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
            image=RemoteFile.from_json(val.get('image')) if val.get('image', None) else None,
            description=val.get('description', None),
            tags=val.get('tags', []),
            refs=[JournalReference.from_json(ref) for ref in val.get('refs', [])],
            authors=[Person.from_json(author) for author in val.get('authors', [])],
            license=License(val.get('license')) if val.get('license', None) else None,
            format=Format.from_json(val.get('format')) if val.get('format', None) else None,
            model=Model.from_json(val.get('model')) if val.get('model', None) else None,
            model_parameter_changes=[ParameterChange.from_json(change, Parameter)
                                     for change in val.get('modelParameterChanges', [])],
            start_time=val.get('startTime', None),
            end_time=val.get('endTime', None),
            num_time_points=val.get('numTimePoints', None),
            algorithm=Algorithm.from_json(val.get('algorithm')) if val.get('algorithm', None) else None,
            algorithm_parameter_changes=[ParameterChange.from_json(change, AlgorithmParameter)
                                         for change in val.get('algorithmParameterChanges', [])]
        )


class Algorithm(object):
    """ Simulation algorithm

    Attributes:
        id (:obj:`str`): KiSAO id
        name (:obj:`str`): name
        parameters (:obj:`list` of :obj:`AlgorithmParameter`): parameters
    """

    def __init__(self, id=None, name=None, parameters=None):
        """
        Args:
            id (:obj:`str`, optional): KiSAO id
            name (:obj:`str`, optional): name
            parameters (:obj:`list` of :obj:`AlgorithmParameter`, optional): parameters
        """
        self.id = id
        self.name = name
        self.parameters = parameters or []

    def __eq__(self, other):
        """ Determine if two algorithms are semantically equal

        Args:
            other (:obj:`Algorithm`): other algorithm

        Returns:
            :obj:`bool`
        """
        return isinstance(other, self.__class__) \
            and self.id == other.id \
            and self.name == other.name \
            and sorted(self.parameters, key=AlgorithmParameter.sort_key) == sorted(other.parameters, key=AlgorithmParameter.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
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
            parameters=[AlgorithmParameter.from_json(param) for param in val.get('parameters', [])],
        )


class AlgorithmParameter(object):
    """ Algorithm parameter

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        type (:obj:`Type`): type
        value (:obj:`object`): value
        kisao_id (:obj:`str`): KiSAO id
    """

    def __init__(self, id=None, name=None, type=None, value=None, kisao_id=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            type (:obj:`Type`, optional): type
            value (:obj:`object`, optional): value
            kisao_id (:obj:`str`, optional): KiSAO id
        """
        self.id = id
        self.name = name
        self.type = type
        self.value = value
        self.kisao_id = kisao_id

    def __eq__(self, other):
        """ Determine if two algorithm parameters are semantically equal

        Args:
            other (:obj:`AlgorithmParameter`): other algorithm parameter

        Returns:
            :obj:`bool`
        """
        return isinstance(other, self.__class__) \
            and self.id == other.id \
            and self.name == other.name \
            and self.type == other.type \
            and self.value == other.value \
            and self.kisao_id == other.kisao_id

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
            'kisaoId': self.kisao_id,
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
            kisao_id=val.get('kisaoId', None),
        )

    @staticmethod
    def sort_key(parameter):
        """ Get a key to sort an algorithm parameter

        Args:
            parameter (:obj:`AlgorithmParameter`): algorithm parameter

        Returns:
            :obj:`tuple`
        """
        return (parameter.id, parameter.name, parameter.type.value if parameter.type else None, parameter.value, parameter.kisao_id)


class ParameterChange(object):
    """ Parameter change

    Attributes:
        parameter (:obj:`Parameter` or :obj:`AlgorithmParameter`): parameter
        value (:obj:`object`): value
    """

    def __init__(self, parameter=None, value=None):
        """
        Args:
            parameter (:obj:`Parameter` or :obj:`AlgorithmParameter`, optional): parameter
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
        return isinstance(other, self.__class__) \
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
            ParameterType (:obj:`types.TypeType`): type of parameter

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
