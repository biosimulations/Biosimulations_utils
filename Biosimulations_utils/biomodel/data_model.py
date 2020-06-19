""" Data model for biomodels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, Identifier, OntologyTerm, RemoteFile, Resource, ResourceMetadata, Taxon, Type, User
import enum
import wc_utils.util.enumerate

__all__ = [
    'BiomodelingFramework',
    'BiomodelFormat',
    'Biomodel',
    'BiomodelParameter',
    'BiomodelVariable',
]


class BiomodelingFramework(enum.Enum):
    flux_balance = OntologyTerm(
        ontology='SBO',
        id='0000624',
        name='flux balance framework',
        description=('Modelling approach, typically used for metabolic models, where the flow '
                     'of metabolites (flux) through a network can be calculated. This approach '
                     'will generally produce a set of solutions (solution space), which may be '
                     'reduced using objective functions and constraints on individual fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000624',
    )

    logical = OntologyTerm(
        ontology='SBO',
        id='0000234',
        name='logical framework',
        description=('Modelling approach, pioneered by Rene Thomas and Stuart Kaufman, where the '
                     'evolution of a system is described by the transitions between discrete activity '
                     'states of "genes" that control each other.'),
        iri='http://biomodels.net/SBO/SBO_0000234',
    )

    non_spatial_continuous = OntologyTerm(
        ontology='SBO',
        id='0000293',
        name='non-spatial continuous framework',
        description=('Modelling approach where the quantities of participants are considered continuous, '
                     'and represented by real values. The associated simulation methods make use of '
                     'differential equations. The models do not take into account the distribution of the '
                     'entities and describe only the temporal fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000293',
    )

    non_spatial_discrete = OntologyTerm(
        ontology='SBO',
        id='0000295',
        name='non-spatial discrete framework',
        description=('Modelling approach where the quantities of participants are considered discrete, '
                     'and represented by integer values. The associated simulation methods can be '
                     'deterministic or stochastic.The models do not take into account the distribution '
                     'of the entities and describe only the temporal fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000295',
    )

    spatial_continuous = OntologyTerm(
        ontology='SBO',
        id='0000292 ',
        name='spatial continuous framework',
        description=('Modelling approach where the quantities of participants are considered continuous, '
                     'and represented by real values. The associated simulation methods make use of '
                     'differential equations. The models take into account the distribution of the '
                     'entities and describe the spatial fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000292 ',
    )

    spatial_discrete = OntologyTerm(
        ontology='SBO',
        id='0000294',
        name='spatial discrete framework',
        description=('Modelling approach where the quantities of participants are considered discrete, '
                     'and represented by integer values. The associated simulation methods can be '
                     'deterministic or stochastic. The models take into account the distribution of '
                     'the entities and describe the spatial fluxes.'),
        iri='http://biomodels.net/SBO/SBO_0000294',
    )


class BiomodelFormat(wc_utils.util.enumerate.CaseInsensitiveEnum):
    """ Model format metadata """
    BNGL = Format(
        id='BNGL',
        name='BioNetGen Language',
        edam_id=None,
        url='https://bionetgen.org/',
        spec_url='https://bionetgen.org/',
        mimetype='text/plain',
        extension='bngl',
    )

    CellML = Format(
        id='CellML',
        name='CellML',
        edam_id='format_3240',
        url='https://bionetgen.org/',
        spec_url='http://identifiers.org/combine.specifications/cellml',
        mimetype='application/cellml+xml',
        extension='cellml',
        sed_urn='urn:sedml:language:cellml',
    )

    Kappa = Format(
        id='Kappa',
        name='Kappa',
        edam_id=None,
        url='https://bionetgen.org/',
        spec_url='https://bionetgen.org/',
        mimetype='text/plain',
        extension='ka',
    )

    MML = Format(
        id='MML',
        name='Multiscale Modeling Language',
        edam_id=None,
        url='https://doi.org/10.1016/j.procs.2010.04.089',
        spec_url='https://doi.org/10.1016/j.procs.2010.04.089',
        mimetype='application/xml',
        extension='xml',
    )

    NeuroML = Format(
        id='NeuroML',
        name='NeuroML',
        edam_id=None,
        url='https://bionetgen.org/',
        spec_url='http://identifiers.org/combine.specifications/neuroml',
        mimetype='application/xml',
        extension='nml',
        sed_urn='urn:sedml:language:neuroml',
    )

    pharmML = Format(
        id='pharmML',
        name='Pharmacometrics Markup Language',
        edam_id=None,
        url='http://www.pharmml.org/',
        spec_url='http://www.pharmml.org/',
        mimetype='application/xml',
        extension='xml',
    )

    SBML = Format(
        id='SBML',
        name='Systems Biology Markup Language',
        edam_id='format_2585',
        url='http://sbml.org/',
        spec_url='http://identifiers.org/combine.specifications/sbml',
        mimetype='application/sbml+xml',
        extension='xml',
        sed_urn='urn:sedml:language:sbml',
    )


class Biomodel(Resource):
    """ A biomodel

    Attributes:
        id (:obj:`str`): id
        file (:obj:`RemoteFile`): file
        format (:obj:`Format`): format
        framework (:obj:`OntologyTerm`): modeling framework
        taxon (:obj:`Taxon`): taxon
        parameters (:obj:`list` of :obj:`BiomodelParameter`): parameters (e.g., initial conditions and rate constants)
        variables (:obj:`list` of :obj:`BiomodelVariable`): variables (e.g., model predictions)
        metadata (:obj:`ResourceMetadata`): metadata
    """

    TYPE = 'model'

    def __init__(self, id=None, file=None, format=None, framework=None, taxon=None, parameters=None, variables=None, metadata=None):
        """
        Args:
            id (:obj:`str`, optional): id
            file (:obj:`RemoteFile`, optional): file
            format (:obj:`Format`, optional): format
            framework (:obj:`OntologyTerm`, optional): modeling framework
            taxon (:obj:`Taxon`, optional): taxon
            parameters (:obj:`list` of :obj:`BiomodelParameter`, optional): parameters (e.g., initial conditions and rate constants)
            variables (:obj:`list` of :obj:`BiomodelVariable`, optional): variables (e.g., model predictions)
            metadata (:obj:`ResourceMetadata`, optional): metadata
        """
        self.id = id
        self.file = file
        self.format = format
        self.framework = framework
        self.taxon = taxon
        self.parameters = parameters or []
        self.variables = variables or []
        self.metadata = metadata or ResourceMetadata()

    def __eq__(self, other):
        """ Determine if two models are semantically equal

        Args:
            other (:obj:`Biomodel`): other model

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.file == other.file \
            and self.format == other.format \
            and self.framework == other.framework \
            and self.taxon == other.taxon \
            and sorted(self.parameters, key=BiomodelParameter.sort_key) == sorted(other.parameters, key=BiomodelParameter.sort_key) \
            and sorted(self.variables, key=BiomodelVariable.sort_key) == sorted(other.variables, key=BiomodelVariable.sort_key) \
            and self.metadata == other.metadata

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        json = {
            'data': {
                'type': self.TYPE,
                'id': self.id,
                'attributes': {
                    'format': self.format.to_json() if self.format else None,
                    'framework': self.framework.to_json() if self.framework else None,
                    'taxon': self.taxon.to_json() if self.taxon else None,
                    'parameters': [parameter.to_json() for parameter in self.parameters],
                    'variables': [variable.to_json() for variable in self.variables],
                    'metadata': self.metadata.to_json() if self.metadata else None,
                },
                'relationships': {
                    'owner': None,
                    'file': None,
                    'image': None,
                    'parent': None,
                },
            },
        }

        if self.metadata.owner:
            json['data']['relationships']['owner'] = {
                'data': {
                    'type': self.metadata.owner.TYPE,
                    'id': self.metadata.owner.id,
                },
            }
        if self.file:
            json['data']['relationships']['file'] = {
                'data': {
                    'type': self.file.TYPE,
                    'id': self.file.id,
                },
            }
        if self.metadata.image:
            json['data']['relationships']['image'] = {
                'data': {
                    'type': self.metadata.image.TYPE,
                    'id': self.metadata.image.id,
                },
            }
        if self.metadata.parent:
            json['data']['relationships']['parent'] = {
                'data': {
                    'type': self.metadata.parent.TYPE,
                    'id': self.metadata.parent.id
                }
            }

        return json

    @classmethod
    def from_json(cls, val):
        """ Create model from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Biomodel`
        """
        data = val.get('data', {})
        if data.get('type', None) != cls.TYPE:
            raise ValueError("`type` '{}' != '{}'".format(data.get('type', ''), cls.TYPE))

        attrs = data.get('attributes', {})
        obj = cls(
            id=data.get('id', None),
            file=RemoteFile.from_json(id=data.get('file')) if data.get('file', None) else None,
            format=Format.from_json(attrs.get('format')) if attrs.get('format', None) else None,
            framework=OntologyTerm.from_json(attrs.get('framework')) if attrs.get('framework', None) else None,
            taxon=Taxon.from_json(attrs.get('taxon')) if attrs.get('taxon', None) else None,
            parameters=[BiomodelParameter.from_json(parameter) for parameter in attrs.get('parameters', [])],
            variables=[BiomodelVariable.from_json(variable) for variable in attrs.get('variables', [])],
            metadata=ResourceMetadata.from_json(attrs.get('metadata')) if attrs.get('metadata', None) else None,
        )

        if data.get('owner', None):
            obj.metadata.owner = User(id=data.get('owner'))
        if data.get('image', None):
            obj.metadata.image = RemoteFile(id=data.get('image'))
        if data.get('parent', None):
            obj.metadata.parent = Biomodel(id=data.get('parent'))

        return obj


class BiomodelParameter(object):
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
            other (:obj:`BiomodelParameter`): other parameter

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
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
            'type': self.type.value if self.type else None,
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
            :obj:`BiomodelParameter`
        """
        return cls(
            target=val.get('target', None),
            group=val.get('group', None),
            id=val.get('id', None),
            name=val.get('name', None),
            description=val.get('description', None),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            type=Type(val.get('type')) if val.get('type', None) else None,
            value=val.get('value', None),
            recommended_range=val.get('recommendedRange', None),
            units=val.get('units', None),
        )

    @staticmethod
    def sort_key(parameter):
        """ Get a key to sort a parameter

        Args:
            parameter (:obj:`BiomodelParameter`): parameter

        Returns:
            :obj:`str`
        """
        return parameter.id


class BiomodelVariable(object):
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
            other (:obj:`BiomodelVariable`): other variable

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
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
            'type': self.type.value if self.type else None,
            'units': self.units,
        }

    @classmethod
    def from_json(cls, val):
        """ Create variable from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`BiomodelVariable`
        """
        return cls(
            target=val.get('target', None),
            group=val.get('group', None),
            id=val.get('id', None),
            name=val.get('name', None),
            description=val.get('description', None),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            type=Type(val.get('type')) if val.get('type', None) else None,
            units=val.get('units', None),
        )

    @staticmethod
    def sort_key(variable):
        """ Get a key to sort a variable

        Args:
            variable (:obj:`BiomodelVariable`): variable

        Returns:
            :obj:`str`
        """
        return variable.id
