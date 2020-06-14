""" Utility clases for data models for models and simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import datetime  # noqa: F401
import dateutil.tz
import enum
import wc_utils.util.enumerate

__all__ = [
    'Format',
    'Identifier',
    'JournalReference',
    'License',
    'OntologyTerm',
    'Person',
    'RemoteFile',
    'ResourceMetadata',
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
        mime_type (:obj:`str`): Multipurpose Internet Mail Extensions (MIME) type. Also known as media type.
        extension (:obj:`str`): file extension (e.g., `xml`)
        sed_urn (:obj:`str`): SED-ML URN
    """

    def __init__(self, id=None, name=None, version=None, edam_id=None, url=None,
                 spec_url=None, mime_type=None, extension=None, sed_urn=None):
        """
        Args:
            id (:obj:`str`, optional): name (e.g., SBML)
            name (:obj:`str`, optional): name (e.g., Systems Biology Markup Language)
            version (:obj:`str`, optional): version (e.g., L3V2)
            edam_id (:obj:`str`, optional): EDAM identifier
            url (:obj:`str`, optional): URL
            spec_url (:obj:`str`, optional): URL for specification
            mime_type (:obj:`str`, optional): Multipurpose Internet Mail Extensions (MIME) type. Also known as media type.
            extension (:obj:`str`, optional): file extension (e.g., `xml`)
            sed_urn (:obj:`str`, optional): SED-ML URN
        """
        self.id = id
        self.name = name
        self.version = version
        self.edam_id = edam_id
        self.url = url
        self.spec_url = spec_url
        self.mime_type = mime_type
        self.extension = extension
        self.sed_urn = sed_urn

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
            and self.spec_url == other.spec_url \
            and self.mime_type == other.mime_type \
            and self.extension == other.extension \
            and self.sed_urn == other.sed_urn

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
            'mimeType': self.mime_type,
            'extension': self.extension,
            'sedUrn': self.sed_urn,
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
            mime_type=val.get('mimeType', None),
            extension=val.get('extension', None),
            sed_urn=val.get('sedUrn', None),
        )

    @staticmethod
    def sort_key(format):
        """ Get a key to sort a format

        Args:
            format (:obj:`Format`): format

        Returns:
            :obj:`tuple`
        """
        return (format.id, format.name, format.version, format.edam_id, format.url,
                format.spec_url, format.mime_type, format.extension, format.sed_urn)


class Identifier(object):
    """ An identifier of a concept

    Attributes:
        namespace (:obj:`str`): namespace (e.g., Identifiers.org namespace such as 'biomodels.db')
        id (:obj:`str`): id within namespace
        url (:obj:`str`): URL
    """

    def __init__(self, namespace=None, id=None, url=None):
        """
        Args:
            namespace (:obj:`str`, optional): namespace (e.g., Identifiers.org namespace such as 'biomodels.db')
            id (:obj:`str`, optional): id within namespace
            url (:obj:`str`, optional): URL
        """
        self.namespace = namespace
        self.id = id
        self.url = url

    def __eq__(self, other):
        """ Determine if two identifiers are semantically equal

        Args:
            other (:obj:`Identifier`): other identifier

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.namespace == other.namespace \
            and self.id == other.id \
            and self.url == other.url \


    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'namespace': self.namespace,
            'id': self.id,
            'url': self.url,
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
            url=val.get('url', None),
        )

    @staticmethod
    def sort_key(identifier):
        """ Get a key to sort an identifier

        Args:
            identifier (:obj:`Identifier`): identifier

        Returns:
            :obj:`tuple`
        """
        return (identifier.namespace, identifier.id, identifier.url)


License = wc_utils.util.enumerate.CaseInsensitiveEnum('License', {
    'cc0': 'CC0',
    'cc_by': 'CC BY',
    'cc_by_sa': 'CC BY-SA',
    'cc_by_nc': 'CC BY-NC',
    'cc_by_nc_sa': 'CC BY-NC-SA',
    'mit': 'MIT',
    'Apache-1.1': 'Apache 1.1',
    'Apache-2.0': 'Apache 2.0',
    'Artistic-1.0': 'Artistic 1.0',
    'Artistic-2.0': 'Artistic 2.0',
    'other': 'Other',
})
""" A license """


class JournalReference(object):
    """ A format

    Attributes:
        authors (:obj:`str`): authors
        title (:obj:`str`): title
        journal (:obj:`str`): journal
        volume (:obj:`int` or :obj:`str`): volume
        issue (:obj:`int`): issue number
        pages (:obj:`str`): pages
        year (:obj:`int`): year
        doi (:obj:`str`): DOI
    """

    def __init__(self, authors=None, title=None, journal=None, volume=None, issue=None, pages=None, year=None, doi=None):
        """
        Args:
            authors (:obj:`str`, optional): authors
            title (:obj:`str`, optional): title
            journal (:obj:`str`, optional): journal
            volume (:obj:`int` or :obj:`str`, optional): volume
            issue (:obj:`int`, optional): issue number
            pages (:obj:`str`, optional): pages
            year (:obj:`int`, optional): year
            doi (:obj:`str`, optional): DOI
        """
        self.authors = authors
        self.title = title
        self.journal = journal
        self.volume = volume
        self.issue = issue
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
            and self.issue == other.issue \
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
            'issue': self.issue,
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
            issue=val.get('issue', None),
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
            ref.issue,
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


class ResourceMetadata(object):
    """ Metadata about a top-level resource such as a model

    Attributes:
        name (:obj:`str`): name
        image (:obj:`RemoteFile`): image file
        description (:obj:`str`): description
        tags (:obj:`list` of :obj:`str`): tags
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        references (:obj:`list` of :obj:`JournalReference`): references
        authors (:obj:`list` of :obj:`Person`): authors
        license (:obj:`License`): license
        created (:obj:`datetime.datetime`): date that the model was created
        updated (:obj:`datetime.datetime`): date that the model was last updated
    """

    def __init__(self, name=None, image=None, description=None, tags=None, identifiers=None,
                 references=None, authors=None, license=None, created=None, updated=None):
        self.name = name
        self.image = image
        self.description = description
        self.tags = tags or []
        self.identifiers = identifiers or []
        self.references = references or []
        self.authors = authors or []
        self.license = license
        self.created = created
        self.updated = updated

    def __eq__(self, other):
        """ Determine if two metadata containers are semantically equal

        Args:
            other (:obj:`ResourceMetadata`): other model

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.name == other.name \
            and self.image == other.image \
            and self.description == other.description \
            and sorted(self.tags) == sorted(other.tags) \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and sorted(self.references, key=JournalReference.sort_key) == sorted(other.references, key=JournalReference.sort_key) \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.license == other.license \
            and self.created == other.created \
            and self.updated == other.updated

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'name': self.name,
            'image': self.image.to_json() if self.image else None,
            'description': self.description,
            'tags': self.tags or [],
            'identifiers': [identifier.to_json() for identifier in self.identifiers],
            'references': [ref.to_json() for ref in self.references],
            'authors': [author.to_json() for author in self.authors],
            'license': self.license.value if self.license else None,
            'created': self.created.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created else None,
            'updated': self.updated.strftime('%Y-%m-%dT%H:%M:%SZ') if self.updated else None,
        }

    @classmethod
    def from_json(cls, val):
        """ Create metadata from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`ResourceMetadata`
        """
        return cls(
            name=val.get('name', None),
            image=RemoteFile.from_json(val.get('image')) if val.get('image', None) else None,
            description=val.get('description', None),
            tags=val.get('tags', []),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            references=[JournalReference.from_json(ref) for ref in val.get('references', [])],
            authors=[Person.from_json(author) for author in val.get('authors', [])],
            license=License(val.get('license')) if val.get('license', None) else None,
            created=dateutil.parser.parse(val.get('created')) if val.get('created', None) else None,
            updated=dateutil.parser.parse(val.get('updated')) if val.get('updated', None) else None,
        )
