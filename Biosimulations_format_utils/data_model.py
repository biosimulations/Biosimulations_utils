""" Utility clases for data models for models and simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum

__all__ = [
    'Format',
    'Identifier',
    'JournalReference',
    'License',
    'OntologyTerm',
    'Person',
    'RemoteFile',
    'Taxon',
    'Type',
]


class Format(object):
    """ A format

    Attributes:
        id (:obj:`str`): name (e.g., SBML)
        name (:obj:`str`): name (e.g., Systems Biology Markup Language)
        version (:obj:`str`): version (e.g., L3V2)
        edam_id (:obj:`str`): EDAM identifier
        url (:obj:`str`): URL
        spec_url (:obj:`str`): URL for specification
    """

    def __init__(self, id=None, name=None, version=None, edam_id=None, url=None, spec_url=None):
        """
        Args:
            id (:obj:`str`, optional): name (e.g., SBML)
            name (:obj:`str`, optional): name (e.g., Systems Biology Markup Language)
            version (:obj:`str`, optional): version (e.g., L3V2)
            edam_id (:obj:`str`, optional): EDAM identifier
            url (:obj:`str`, optional): URL
            spec_url (:obj:`str`): URL for specification
        """
        self.id = id
        self.name = name
        self.version = version
        self.edam_id = edam_id
        self.url = url
        self.spec_url = spec_url

    def __eq__(self, other):
        """ Determine if two formats are semantically equal

        Args:
            other (:obj:`Format`): other format

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and self.version == other.version \
            and self.edam_id == other.edam_id \
            and self.url == other.url \
            and self.spec_url == other.spec_url

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'edamId': self.edam_id,
            'url': self.url,
            'specUrl': self.spec_url,
        }

    @classmethod
    def from_json(cls, val):
        """ Create format from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Format`
        """
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
            version=val.get('version', None),
            edam_id=val.get('edamId', None),
            url=val.get('url', None),
            spec_url=val.get('specUrl', None),
        )

    @staticmethod
    def sort_key(format):
        """ Get a key to sort a format

        Args:
            format (:obj:`Format`): format

        Returns:
            :obj:`tuple`
        """
        return (format.id, format.name, format.version, format.edam_id, format.url, format.spec_url)


class Identifier(object):
    """ An identifier of a concept

    Attributes:
        namespace (:obj:`str`): namespace (e.g., Identifiers.org namespace such as 'biomodels.db')
        id (:obj:`str`): id within namespace
    """

    def __init__(self, namespace=None, id=None):
        """
        Args:
            namespace (:obj:`str`, optional): namespace (e.g., Identifiers.org namespace such as 'biomodels.db')
            id (:obj:`str`, optional): id within namespace
        """
        self.namespace = namespace
        self.id = id

    def __eq__(self, other):
        """ Determine if two identifiers are semantically equal

        Args:
            other (:obj:`Identifier`): other identifier

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.namespace == other.namespace \
            and self.id == other.id

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'namespace': self.namespace,
            'id': self.id,
        }

    @classmethod
    def from_json(cls, val):
        """ Create an identifier from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Identifier`
        """
        return cls(
            namespace=val.get('namespace', None),
            id=val.get('id', None),
        )

    @staticmethod
    def sort_key(identifier):
        """ Get a key to sort an identifier

        Args:
            identifier (:obj:`Identifier`): identifier

        Returns:
            :obj:`tuple`
        """
        return (identifier.namespace, identifier.id)


class License(str, enum.Enum):
    """ A license """
    cc0 = 'CC0'
    cc_by = 'CC BY'
    cc_by_sa = 'CC BY-SA'
    cc_by_nc = 'CC BY-NC'
    cc_by_nc_sa = 'CC BY-NC-SA'
    mit = 'MIT'
    other = 'Other'


class JournalReference(object):
    """ A format

    Attributes:
        authors (:obj:`str`): authors
        title (:obj:`str`): title
        journal (:obj:`str`): journal
        volume (:obj:`int` or :obj:`str`): volume
        num (:obj:`int`): issue number
        pages (:obj:`str`): pages
        year (:obj:`int`): year
        doi (:obj:`str`): DOI
    """

    def __init__(self, authors=None, title=None, journal=None, volume=None, num=None, pages=None, year=None, doi=None):
        """
        Args:
            authors (:obj:`str`, optional): authors
            title (:obj:`str`, optional): title
            journal (:obj:`str`, optional): journal
            volume (:obj:`int` or :obj:`str`, optional): volume
            num (:obj:`int`, optional): issue number
            pages (:obj:`str`, optional): pages
            year (:obj:`int`, optional): year
            doi (:obj:`str`, optional): DOI
        """
        self.authors = authors
        self.title = title
        self.journal = journal
        self.volume = volume
        self.num = num
        self.pages = pages
        self.year = year
        self.doi = doi

    def __eq__(self, other):
        """ Determine if two formats are semantically equal

        Args:
            other (:obj:`Format`): other format

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.authors == other.authors \
            and self.title == other.title \
            and self.journal == other.journal \
            and self.volume == other.volume \
            and self.num == other.num \
            and self.pages == other.pages \
            and self.year == other.year \
            and self.doi == other.doi

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'authors': self.authors,
            'title': self.title,
            'journal': self.journal,
            'volume': self.volume,
            'num': self.num,
            'pages': self.pages,
            'year': self.year,
            'doi': self.doi,
        }

    @classmethod
    def from_json(cls, val):
        """ Create journal reference from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`JournalReference`
        """
        return cls(
            authors=val.get('authors', None),
            title=val.get('title', None),
            journal=val.get('journal', None),
            volume=val.get('volume', None),
            num=val.get('num', None),
            pages=val.get('pages', None),
            year=val.get('year', None),
            doi=val.get('doi', None),
        )

    @staticmethod
    def sort_key(ref):
        """ Get a key to sort a reference

        Args:
            ref (:obj:`JournalReference`): reference

        Returns:
            :obj:`tuple`
        """
        return (
            ref.authors,
            ref.title,
            ref.journal,
            ref.volume,
            ref.num,
            ref.pages,
            ref.year,
            ref.doi,
        )


class OntologyTerm(object):
    """ A term in an ontology

    Attributes:
        ontology (:obj:`str`): id of the parent ontology
        id (:obj:`str`): id
        name (:obj:`str`): name
        description (:obj:`str`): description
        iri (:obj:`str`): IRI
    """

    def __init__(self, ontology=None, id=None, name=None, description=None, iri=None):
        """
        Args:
            ontology (:obj:`str`, optional): id of the parent ontology
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            description (:obj:`str`, optional): description
            iri (:obj:`str`, optional): IRI
        """
        self.ontology = ontology
        self.id = id
        self.name = name
        self.description = description
        self.iri = iri

    def __eq__(self, other):
        """ Determine if two ontology terms are semantically equal

        Args:
            other (:obj:`OntologyTerm`): other term

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.ontology == other.ontology \
            and self.id == other.id \
            and self.name == other.name \
            and self.description == other.description \
            and self.iri == other.iri

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'ontology': self.ontology,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'iri': self.iri,
        }

    @classmethod
    def from_json(cls, val):
        """ Create an ontology term from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`OntologyTerm`
        """
        return cls(
            ontology=val.get('ontology', None),
            id=val.get('id', None),
            name=val.get('name', None),
            description=val.get('description', None),
            iri=val.get('iri', None),
        )

    @staticmethod
    def sort_key(term):
        """ Get a key to sort an ontology term

        Args:
            term (:obj:`OntologyTerm`): term

        Returns:
            :obj:`tuple`
        """
        return (term.ontology, term.id, term.name, term.description, term.iri)


class Person(object):
    """ A person, such as an author of a journal article

    Attributes:
        first_name (:obj:`str`): first name
        middle_name (:obj:`str`): middle name
        last_name (:obj:`str`): last name
    """

    def __init__(self, first_name=None, middle_name=None, last_name=None):
        """
        Args:
            first_name (:obj:`str`, optional): first name
            middle_name (:obj:`str`, optional): middle name
            last_name (:obj:`str`, optional): last name
        """
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name

    def __eq__(self, other):
        """ Determine if two formats are semantically equal

        Args:
            other (:obj:`Format`): other format

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.first_name == other.first_name \
            and self.middle_name == other.middle_name \
            and self.last_name == other.last_name

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'firstName': self.first_name,
            'middleName': self.middle_name,
            'lastName': self.last_name,
        }

    @classmethod
    def from_json(cls, val):
        """ Create person from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Person`
        """
        return cls(
            first_name=val.get('firstName', None),
            middle_name=val.get('middleName', None),
            last_name=val.get('lastName', None),
        )

    @staticmethod
    def sort_key(person):
        """ Get a key to sort a person

        Args:
            person (:obj:`Person`): person

        Returns:
            :obj:`tuple`
        """
        return (person.last_name, person.first_name, person.middle_name)


class RemoteFile(object):
    """ A remote file

    Attributes:
        name (:obj:`str`): name (e.g., model.xml)
        type (:obj:`str`): MIME type (e.g., application/sbml+xml)
        size (:obj:`int`): size in bytes
    """

    def __init__(self, name=None, type=None, size=None):
        """
        Args:
            name (:obj:`str`, optional): name (e.g., model.xml)
            type (:obj:`str`, optional): MIME type (e.g., application/sbml+xml)
            size (:obj:`int`, optional): size in bytes
        """
        self.name = name
        self.type = type
        self.size = size

    def __eq__(self, other):
        """ Determine if two formats are semantically equal

        Args:
            other (:obj:`Format`): other format

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.name == other.name \
            and self.type == other.type \
            and self.size == other.size

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'name': self.name,
            'type': self.type,
            'size': self.size,
        }

    @classmethod
    def from_json(cls, val):
        """ Create a remote file from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`RemoteFile`
        """
        return cls(
            name=val.get('name', None),
            type=val.get('type', None),
            size=val.get('size', None),
        )


class Taxon(object):
    """ A taxon in the NCBI Taxonomy database

    Attributes:
        id (:obj:`int`): id
        name (:obj:`str`): name
    """

    def __init__(self, id=None, name=None):
        """
        Args:
            id (:obj:`int`, optional): id
            name (:obj:`str`, optional): name
        """
        self.id = id
        self.name = name

    def __eq__(self, other):
        """ Determine if two taxa are semantically equal

        Args:
            other (:obj:`Taxon`): other taxon

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
        }

    @classmethod
    def from_json(cls, val):
        """ Create a taxon from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Taxon`
        """
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
        )


class Type(str, enum.Enum):
    """ A type """
    boolean = 'boolean'
    integer = 'integer'
    float = 'float'
    string = 'string'
