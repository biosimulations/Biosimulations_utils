""" Utility clases for data models for models and simulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-31
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .utils import time_since_epoch_to_datetime, datetime_to_time_since_epoch
import datetime  # noqa: F401
import enum
import wc_utils.util.enumerate

__all__ = [
    'AccessLevel',
    'Format',
    'Identifier',
    'JournalCitation',
    'License',
    'OntologyTerm',
    'Person',
    'PrimaryResource',
    'PrimaryResourceMetadata',
    'RemoteFile',
    'Resource',
    'ResourceMetadata',
    'ResourceReferences',
    'Taxon',
    'Type',
    'User',
]


class Resource(object):
    """ A resource

    Attributes:
        id (:obj:`str`): id
        _metadata (:obj:`ResourceMetadata`): private metadata
    """
    TYPE = None


class PrimaryResource(Resource):
    """ A primary resource

    Attributes:
        metadata (:obj:`PrimaryResourceMetadata`): public metadata
    """
    pass


class Format(object):
    """ A format

    Attributes:
        id (:obj:`str`): name (e.g., SBML)
        name (:obj:`str`): name (e.g., Systems Biology Markup Language)
        version (:obj:`str`): version (e.g., L3V2)
        edam_id (:obj:`str`): EDAM identifier
        url (:obj:`str`): URL
        spec_url (:obj:`str`): URL for specification
        mimetype (:obj:`str`): Multipurpose Internet Mail Extensions (MIME) type. Also known as media type.
        extension (:obj:`str`): file extension (e.g., `xml`)
        sed_urn (:obj:`str`): SED-ML URN
    """

    def __init__(self, id=None, name=None, version=None, edam_id=None, url=None,
                 spec_url=None, mimetype=None, extension=None, sed_urn=None):
        """
        Args:
            id (:obj:`str`, optional): name (e.g., SBML)
            name (:obj:`str`, optional): name (e.g., Systems Biology Markup Language)
            version (:obj:`str`, optional): version (e.g., L3V2)
            edam_id (:obj:`str`, optional): EDAM identifier
            url (:obj:`str`, optional): URL
            spec_url (:obj:`str`, optional): URL for specification
            mimetype (:obj:`str`, optional): Multipurpose Internet Mail Extensions (MIME) type. Also known as media type.
            extension (:obj:`str`, optional): file extension (e.g., `xml`)
            sed_urn (:obj:`str`, optional): SED-ML URN
        """
        self.id = id
        self.name = name
        self.version = version
        self.edam_id = edam_id
        self.url = url
        self.spec_url = spec_url
        self.mimetype = mimetype
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
            and self.mimetype == other.mimetype \
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
            'mimetype': self.mimetype,
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
            mimetype=val.get('mimetype', None),
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
                format.spec_url, format.mimetype, format.extension, format.sed_urn)


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


class JournalCitation(object):
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
            :obj:`JournalCitation`
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
    def sort_key(citation):
        """ Get a key to sort a reference

        Args:
            citation (:obj:`JournalCitation`): reference

        Returns:
            :obj:`tuple`
        """
        return (
            citation.authors,
            citation.title,
            citation.journal,
            citation.volume,
            citation.issue,
            citation.pages,
            citation.year,
            citation.doi,
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


class User(Resource):
    """ A user

    Attributes:
        id (:obj:`str`): id
    """
    TYPE = 'user'

    def __init__(self, id=None):
        """
        Args:
            id (:obj:`str`, optional): id
        """
        self.id = id

    def __eq__(self, other):
        """ Determine if two users are semantically equal

        Args:
            other (:obj:`User`): other user

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'data': {
                'type': self.TYPE,
                'id': self.id
            }
        }

    @classmethod
    def from_json(cls, val):
        """ Create a user from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`User`
        """
        if val is None or val.get('data', None) is None:
            return None

        data = val.get('data', {})
        if data.get('type', None) != cls.TYPE:
            raise ValueError("`type` '{}' != '{}'".format(data.get('type', ''), cls.TYPE))
        return cls(
            id=data.get('id', None)
        )


class RemoteFile(Resource):
    """ A remote file

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name (e.g., model.xml)
        type (:obj:`str`): MIME type (e.g., application/sbml+xml)
        size (:obj:`int`): size in bytes
    """
    TYPE = 'file'

    def __init__(self, id=None, name=None, type=None, size=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name (e.g., model.xml)
            type (:obj:`str`, optional): MIME type (e.g., application/sbml+xml)
            size (:obj:`int`, optional): size in bytes
        """
        self.id = id
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
            and self.id == other.id \
            and self.name == other.name \
            and self.type == other.type \
            and self.size == other.size

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'data': {
                'type': self.TYPE,
                'id': self.id,
                'attributes': {
                    'name': self.name,
                    'type': self.type,
                    'size': self.size,
                },
            }
        }

    @classmethod
    def from_json(cls, val):
        """ Create a remote file from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`RemoteFile`
        """
        if val is None or val.get('data', None) is None:
            return None

        data = val.get('data', {})
        if data.get('type', None) != cls.TYPE:
            raise ValueError("`type` '{}' != '{}'".format(data.get('type', ''), cls.TYPE))

        attrs = data.get('attributes', {})
        return cls(
            id=data.get('id', None),
            name=attrs.get('name', None),
            type=attrs.get('type', None),
            size=attrs.get('size', None),
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


class AccessLevel(wc_utils.util.enumerate.CaseInsensitiveEnum):
    """ An access level """
    private = 'private'
    public = 'public'
    protected = 'password protected'


class ResourceMetadata(object):
    """ Metadata about a top-level resource such as a model

    Attributes:
        version (:obj:`int`): version
        created (:obj:`datetime.datetime`): date that the model was created
        updated (:obj:`datetime.datetime`): date that the model was last updated
    """

    def __init__(self, version=None, created=None, updated=None):
        """
        Args:
            version (:obj:`int`): version
            created (:obj:`datetime.datetime`, optional): date that the model was created
            updated (:obj:`datetime.datetime`, optional): date that the model was last updated
        """
        self.version = version
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
            and self.version == other.version \
            and self.created == other.created \
            and self.updated == other.updated

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'version': self.version,
            'created': datetime_to_time_since_epoch(self.created) if self.created else None,
            'updated': datetime_to_time_since_epoch(self.updated) if self.updated else None,
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
            version=val.get('version', None),
            created=time_since_epoch_to_datetime(val.get('created')) if val.get('created', None) else None,
            updated=time_since_epoch_to_datetime(val.get('updated')) if val.get('updated', None) else None,
        )


class PrimaryResourceMetadata(object):
    """ Metadata about a top-level resource such as a model

    Attributes:
        name (:obj:`str`): name
        image (:obj:`RemoteFile`): image file
        summary (:obj:`str`): short description
        description (:obj:`str`): description
        tags (:obj:`list` of :obj:`str`): tags
        references (:obj:`ResourceReferences`): external references
        authors (:obj:`list` of :obj:`Person`): authors
        parent (:obj:`object`): parent resource
        license (:obj:`License`): license
        owner (:obj:`User`): owner
        access_level (:obj:`AccessLevel`): access level
    """

    def __init__(self, name=None, image=None, summary=None, description=None, tags=None,
                 references=None, authors=None, parent=None, license=None, owner=None,
                 access_level=AccessLevel.private):
        """
        Args:
            name (:obj:`str`, optional): name
            image (:obj:`RemoteFile`, optional): image file
            summary (:obj:`str`, optional): short description
            description (:obj:`str`, optional): description
            tags (:obj:`list` of :obj:`str`, optional): tags
            references (:obj:`ResourceReferences`, optional): external references
            authors (:obj:`list` of :obj:`Person`, optional): authors
            parent (:obj:`object`, optional): parent resource
            license (:obj:`License`, optional): license
            owner (:obj:`user`, optional): owner
            access_level (:obj:`AccessLevel`, optional): access level
        """
        self.name = name
        self.image = image
        self.summary = summary
        self.description = description
        self.tags = tags or []
        self.references = references or ResourceReferences()
        self.authors = authors or []
        self.parent = parent
        self.license = license
        self.owner = owner
        self.access_level = access_level

    def __eq__(self, other):
        """ Determine if two metadata containers are semantically equal

        Args:
            other (:obj:`PrimaryResourceMetadata`): other model

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.name == other.name \
            and self.image == other.image \
            and self.summary == other.summary \
            and self.description == other.description \
            and sorted(self.tags) == sorted(other.tags) \
            and self.references == other.references \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.parent == other.parent \
            and self.license == other.license \
            and self.owner == other.owner \
            and self.access_level == other.access_level

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'name': self.name,
            'summary': self.summary,
            'description': self.description,
            'tags': self.tags or [],
            'references': self.references.to_json(),
            'authors': [author.to_json() for author in self.authors],
            'license': self.license.value if self.license else None,
            'accessLevel': self.access_level.value if self.access_level else None,
        }

    @classmethod
    def from_json(cls, val):
        """ Create metadata from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`PrimaryResourceMetadata`
        """
        return cls(
            name=val.get('name', None),
            summary=val.get('summary', None),
            description=val.get('description', None),
            tags=val.get('tags', []),
            references=ResourceReferences.from_json(val.get('references')) if val.get('references', None) else None,
            authors=[Person.from_json(author) for author in val.get('authors', [])],
            license=License(val.get('license')) if val.get('license', None) else None,
            access_level=AccessLevel(val.get('accessLevel')) if val.get('accessLevel', None) else None,
        )


class ResourceReferences(object):
    """ External references for a resource

    Attributes:
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        citations (:obj:`list` of :obj:`JournalCitation`): citations
        doi (:obj:`str`): DOI
    """

    def __init__(self, identifiers=None, citations=None, doi=None):
        self.identifiers = identifiers or []
        self.citations = citations or []
        self.doi = doi

    def __eq__(self, other):
        """ Determine if two metadata containers are semantically equal

        Args:
            other (:obj:`ResourceReferences`): other model

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and sorted(self.citations, key=JournalCitation.sort_key) == sorted(other.citations, key=JournalCitation.sort_key) \
            and self.doi == other.doi

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'identifiers': [identifier.to_json() for identifier in self.identifiers],
            'citations': [ref.to_json() for ref in self.citations],
            'doi': self.doi
        }

    @classmethod
    def from_json(cls, val):
        """ Create metadata from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`ResourceReferences`
        """
        return cls(
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            citations=[JournalCitation.from_json(ref) for ref in val.get('citations', [])],
            doi=val.get('doi', None),
        )
