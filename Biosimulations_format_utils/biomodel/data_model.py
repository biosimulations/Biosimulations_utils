""" Data model for biomodels

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, Identifier, JournalReference, License, OntologyTerm, Person, RemoteFile, Taxon, Type
import datetime  # noqa: F401
import dateutil.parser
import wc_utils.util.enumerate

__all__ = [
    'BiomodelFormat',
    'Biomodel',
    'BiomodelParameter',
    'BiomodelVariable',
]


class BiomodelFormat(wc_utils.util.enumerate.CaseInsensitiveEnum):
    """ Model format metadata """
    BNGL = Format(
        id='BNGL',
        name='BioNetGen Language',
        edam_id=None,
        url='https://bionetgen.org/',
        spec_url='https://bionetgen.org/',
        mime_type='text/plain',
        extension='bngl',
    )

    CellML = Format(
        id='CellML',
        name='CellML',
        edam_id='format_3240',
        url='https://bionetgen.org/',
        spec_url='http://identifiers.org/combine.specifications/cellml',
        mime_type='application/cellml+xml',
        extension='cellml',
        sed_urn='urn:sedml:language:cellml',
    )

    Kappa = Format(
        id='Kappa',
        name='Kappa',
        edam_id=None,
        url='https://bionetgen.org/',
        spec_url='https://bionetgen.org/',
        mime_type='text/plain',
        extension='ka',
    )

    MML = Format(
        id='MML',
        name='Multiscale Modeling Language',
        edam_id=None,
        url='https://doi.org/10.1016/j.procs.2010.04.089',
        spec_url='https://doi.org/10.1016/j.procs.2010.04.089',
        mime_type='application/xml',
        extension='xml',
    )

    NeuroML = Format(
        id='NeuroML',
        name='NeuroML',
        edam_id=None,
        url='https://bionetgen.org/',
        spec_url='http://identifiers.org/combine.specifications/neuroml',
        mime_type='application/xml',
        extension='nml',
        sed_urn='urn:sedml:language:neuroml',
    )

    pharmML = Format(
        id='pharmML',
        name='Pharmacometrics Markup Language',
        edam_id=None,
        url='http://www.pharmml.org/',
        spec_url='http://www.pharmml.org/',
        mime_type='application/xml',
        extension='xml',
    )

    SBML = Format(
        id='SBML',
        name='Systems Biology Markup Language',
        edam_id='format_2585',
        url='http://sbml.org/',
        spec_url='http://identifiers.org/combine.specifications/sbml',
        mime_type='application/sbml+xml',
        extension='xml',
        sed_urn='urn:sedml:language:sbml',
    )


class Biomodel(object):
    """ A biomodel

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        file (:obj:`RemoteFile`): file
        image (:obj:`RemoteFile`): image file
        description (:obj:`str`): description
        format (:obj:`Format`): format
        framework (:obj:`OntologyTerm`): modeling framework
        taxon (:obj:`Taxon`): taxon
        tags (:obj:`list` of :obj:`str`): tags
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        references (:obj:`list` of :obj:`JournalReference`): references
        authors (:obj:`list` of :obj:`Person`): authors
        license (:obj:`License`): license
        parameters (:obj:`list` of :obj:`BiomodelParameter`): parameters (e.g., initial conditions and rate constants)
        variables (:obj:`list` of :obj:`BiomodelVariable`): variables (e.g., model predictions)
        created (:obj:`datetime.datetime`): date that the model was created
        updated (:obj:`datetime.datetime`): date that the model was last updated
    """

    def __init__(self, id=None, name=None, file=None, image=None, description=None,
                 format=None, framework=None, taxon=None, tags=None,
                 identifiers=None, references=None, authors=None, license=None,
                 parameters=None, variables=None, created=None, updated=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            file (:obj:`RemoteFile`, optional): file
            image (:obj:`RemoteFile`, optional): image file
            description (:obj:`str`, optional): description
            format (:obj:`Format`, optional): format
            framework (:obj:`OntologyTerm`, optional): modeling framework
            taxon (:obj:`Taxon`, optional): taxon
            tags (:obj:`list` of :obj:`str`, optional): tags
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            references (:obj:`list` of :obj:`JournalReference`, optional): references
            authors (:obj:`list` of :obj:`Person`, optional): authors
            license (:obj:`License`, optional): license
            parameters (:obj:`list` of :obj:`BiomodelParameter`, optional): parameters (e.g., initial conditions and rate constants)
            variables (:obj:`list` of :obj:`BiomodelVariable`, optional): variables (e.g., model predictions)
            created (:obj:`datetime.datetime`, optional): date that the model was created
            updated (:obj:`datetime.datetime`, optional): date that the model was last updated
        """
        self.id = id
        self.name = name
        self.file = file
        self.image = image
        self.description = description
        self.format = format
        self.framework = framework
        self.taxon = taxon
        self.tags = tags or []
        self.identifiers = identifiers or []
        self.references = references or []
        self.authors = authors or []
        self.license = license
        self.parameters = parameters or []
        self.variables = variables or []
        self.created = created
        self.updated = updated

    def __eq__(self, other):
        """ Determine if two models are semantically equal

        Args:
            other (:obj:`Biomodel`): other model

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and self.file == other.file \
            and self.image == other.image \
            and self.description == other.description \
            and self.format == other.format \
            and self.framework == other.framework \
            and self.taxon == other.taxon \
            and sorted(self.tags) == sorted(other.tags) \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and sorted(self.references, key=JournalReference.sort_key) == sorted(other.references, key=JournalReference.sort_key) \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.license == other.license \
            and sorted(self.parameters, key=BiomodelParameter.sort_key) == sorted(other.parameters, key=BiomodelParameter.sort_key) \
            and sorted(self.variables, key=BiomodelVariable.sort_key) == sorted(other.variables, key=BiomodelVariable.sort_key) \
            and self.created == other.created \
            and self.updated == other.updated

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
            'file': self.file.to_json() if self.file else None,
            'image': self.image.to_json() if self.image else None,
            'description': self.description,
            'format': self.format.to_json() if self.format else None,
            'framework': self.framework.to_json() if self.framework else None,
            'taxon': self.taxon.to_json() if self.taxon else None,
            'tags': self.tags or [],
            'identifiers': [identifier.to_json() for identifier in self.identifiers],
            'references': [ref.to_json() for ref in self.references],
            'authors': [author.to_json() for author in self.authors],
            'license': self.license.value if self.license else None,
            'parameters': [parameter.to_json() for parameter in self.parameters],
            'variables': [variable.to_json() for variable in self.variables],
            'created': self.created.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created else None,
            'updated': self.updated.strftime('%Y-%m-%dT%H:%M:%SZ') if self.updated else None,
        }

    @classmethod
    def from_json(cls, val):
        """ Create model from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Biomodel`
        """
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
            file=RemoteFile.from_json(val.get('file')) if val.get('file', None) else None,
            image=RemoteFile.from_json(val.get('image')) if val.get('image', None) else None,
            description=val.get('description', None),
            format=Format.from_json(val.get('format')) if val.get('format', None) else None,
            framework=OntologyTerm.from_json(val.get('framework')) if val.get('framework', None) else None,
            taxon=Taxon.from_json(val.get('taxon')) if val.get('taxon', None) else None,
            tags=val.get('tags', []),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            references=[JournalReference.from_json(ref) for ref in val.get('references', [])],
            authors=[Person.from_json(author) for author in val.get('authors', [])],
            license=License(val.get('license')) if val.get('license', None) else None,
            parameters=[BiomodelParameter.from_json(parameter) for parameter in val.get('parameters', [])],
            variables=[BiomodelVariable.from_json(variable) for variable in val.get('variables', [])],
            created=dateutil.parser.parse(val.get('created')) if val.get('created', None) else None,
            updated=dateutil.parser.parse(val.get('updated')) if val.get('updated', None) else None,
        )


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
