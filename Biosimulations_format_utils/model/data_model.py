""" Data model for biomodels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, Identifier, OntologyTerm, Taxon, Type

__all__ = [
    'Model',
    'Parameter',
    'Variable',
]


class Model(object):
    """ A biomodel

    Attributes:
        format (:obj:`Format`): format
        framework (:obj:`OntologyTerm`): modeling framework
        taxon (:obj:`Taxon`): taxon
        parameters (:obj:`list` of :obj:`Parameter`): parameters (e.g., initial conditions and rate constants)
        variables (:obj:`list` of :obj:`Variable`): variables (e.g., model predictions)
    """

    def __init__(self, format=None, framework=None, taxon=None, parameters=None, variables=None):
        """
        Args:
            format (:obj:`Format`, optional): format
            framework (:obj:`OntologyTerm`, optional): modeling framework
            taxon (:obj:`Taxon`, optional): taxon
            parameters (:obj:`list` of :obj:`Parameter`, optional): parameters (e.g., initial conditions and rate constants)
            variables (:obj:`list` of :obj:`Variable`, optional): variables (e.g., model predictions)
        """
        self.format = format
        self.framework = framework
        self.taxon = taxon
        self.parameters = parameters or []
        self.variables = variables or []

    def __eq__(self, other):
        """ Determine if two models are semantically equal

        Args:
            other (:obj:`Model`): other model

        Returns:
            :obj:`bool`
        """
        return isinstance(other, self.__class__) \
            and self.format == other.target \
            and self.framework == other.group \
            and self.taxon == other.id \
            and sorted(self.parameters, key=Parameter.sort_key) == sorted(other.parameters, key=Parameter.sort_key) \
            and sorted(self.variables, key=Variable.sort_key) == sorted(other.variables, key=Variable.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'format': self.format.to_json() if self.format else None,
            'framework': self.framework.to_json() if self.framework else None,
            'taxon': self.taxon.to_json() if self.taxon else None,
            'parameters': [parameter.to_json() for parameter in self.parameters],
            'variables': [variable.to_json() for variable in self.variables],
        }

    @classmethod
    def from_json(cls, val):
        """ Create model from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Model`
        """
        return cls(
            format=Format.from_json(val.get('format')) if 'format' in val else None,
            framework=OntologyTerm.from_json(val.get('framework')) if 'framework' in val else None,
            taxon=Taxon.from_json(val.get('taxon')) if 'taxon' in val else None,
            parameters=[Parameter.from_json(parameter) for parameter in val.get('parameters', [])],
            variables=[Variable.from_json(variable) for variable in val.get('variables', [])],
        )


class Parameter(object):
    """ A parameter of a model

    Attributes:
        target (:obj:`str`): address within the model (e.g., XML path)
        group (:obj:`str`): Name of the group that the parameter belongs to (e.g., 'Initial species amounts/concentrations').
            Used to organize the display of parameters in the BioSimulations user interface.
        id (:obj:`str`): id
        name (:obj:`str`): name
        description (:obj:`str`): description
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        type (:obj:`Type`): type of :obj:`value`
        value (:obj:`object`): :obj:`value`
        recommended_range (:obj:`list` of :obj:`object`): minimum and maximum recommended values of :obj:`value`
        units (:obj:`str`): units of :obj:`value`
    """

    def __init__(self, target=None, group=None, id=None, name=None, description=None,
                 identifiers=None, type=None, value=None, recommended_range=None, units=None):
        """
        Args:
            target (:obj:`str`, optional): address within the model (e.g., XML path)
            group (:obj:`str`, optional): Name of the group that the parameter belongs to (e.g., 'Initial species amounts/concentrations').
                Used to organize the display of parameters in the BioSimulations user interface.
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            description (:obj:`str`, optional): description
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            type (:obj:`Type`, optional): type of :obj:`value`
            value (:obj:`object`, optional): :obj:`value`
            recommended_range (:obj:`list` of :obj:`object`, optional): minimum and maximum recommended values of :obj:`value`
            units (:obj:`str`, optional): units of :obj:`value`
        """
        self.target = target
        self.group = group
        self.id = id
        self.name = name
        self.description = description
        self.identifiers = identifiers or []
        self.type = type
        self.value = value
        self.recommended_range = recommended_range
        self.units = units

    def __eq__(self, other):
        """ Determine if two parameters are semantically equal

        Args:
            other (:obj:`Parameter`): other parameter

        Returns:
            :obj:`bool`
        """
        return isinstance(other, self.__class__) \
            and self.target == other.target \
            and self.group == other.group \
            and self.id == other.id \
            and self.name == other.name \
            and self.description == other.description \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and self.type == other.type \
            and self.value == other.value \
            and self.recommended_range == other.recommended_range \
            and self.units == other.units

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'target': self.target,
            'group': self.group,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'identifiers': list(identifier.to_json() for identifier in self.identifiers),
            'type': self.type.name if self.type else None,
            'value': self.value,
            'recommendedRange': self.recommended_range,
            'units': self.units,
        }

    @classmethod
    def from_json(cls, val):
        """ Create parameter from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Parameter`
        """
        return cls(
            target=val.get('target', None),
            group=val.get('group', None),
            id=val.get('id', None),
            name=val.get('name', None),
            description=val.get('description', None),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            type=Type[val.get('type')] if 'type' in val else None,
            value=val.get('value', None),
            recommended_range=val.get('recommendedRange', None),
            units=val.get('units', None),
        )

    @staticmethod
    def sort_key(parameter):
        """ Get a key to sort a parameter

        Args:
            parameter (:obj:`Parameter`): parameter

        Returns:
            :obj:`str`
        """
        return parameter.id


class Variable(object):
    """ A variable of a model

    Attributes:
        target (:obj:`str`): address within the model (e.g., XML path)
        group (:obj:`str`): Name of the group that the variable belongs to (e.g., 'Species amounts/concentrations').
            Used to organize the display of variable in the BioSimulations user interface.
        id (:obj:`str`): id
        name (:obj:`str`): name
        description (:obj:`str`): description
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        type (:obj:`Type`): type of :obj:`value`
        units (:obj:`str`): units of :obj:`value`
    """

    def __init__(self, target=None, group=None, id=None, name=None, description=None,
                 identifiers=None, type=None, units=None):
        """
        Args:
            target (:obj:`str`, optional): address within the model (e.g., XML path)
            group (:obj:`str`): Name of the group that the variable belongs to (e.g., 'Species amounts/concentrations').
            Used to organize the display of variable in the BioSimulations user interface.
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            description (:obj:`str`, optional): description
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            type (:obj:`Type`, optional): type of :obj:`value`
            units (:obj:`str`, optional): units of :obj:`value`
        """
        self.target = target
        self.group = group
        self.id = id
        self.name = name
        self.description = description
        self.identifiers = identifiers or []
        self.type = type
        self.units = units

    def __eq__(self, other):
        """ Determine if two variables are semantically equal

        Args:
            other (:obj:`Variable`): other variable

        Returns:
            :obj:`bool`
        """
        return isinstance(other, self.__class__) \
            and self.target == other.target \
            and self.group == other.group \
            and self.id == other.id \
            and self.name == other.name \
            and self.description == other.description \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and self.type == other.type \
            and self.units == other.units

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'target': self.target,
            'group': self.group,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'identifiers': list(identifier.to_json() for identifier in self.identifiers),
            'type': self.type.name if self.type else None,
            'units': self.units,
        }

    @classmethod
    def from_json(cls, val):
        """ Create variable from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Variable`
        """
        return cls(
            target=val.get('target', None),
            group=val.get('group', None),
            id=val.get('id', None),
            name=val.get('name', None),
            description=val.get('description', None),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            type=Type[val.get('type')] if 'type' in val else None,
            units=val.get('units', None),
        )

    @staticmethod
    def sort_key(variable):
        """ Get a key to sort a variable

        Args:
            variable (:obj:`Variable`): variable

        Returns:
            :obj:`str`
        """
        return variable.id
