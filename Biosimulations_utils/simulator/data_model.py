""" Data model for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, Identifier, JournalReference, License, Person, RemoteFile
from ..simulation.data_model import Algorithm
import datetime  # noqa: F401
import dateutil.tz

__all__ = ['Simulator']


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
        docker_hub_image_id (:obj:`str`): id for image in DockerHub (e.g., "crbm/biosimulations_tellurium:2.4.1")
        algorithms (:obj:`list` of :obj:`Algorithm`): supported algorithms
        created (:obj:`datetime.datetime`): date that the simulator was created
        updated (:obj:`datetime.datetime`): date that the simulator was last updated
    """

    def __init__(self, id=None, name=None, version=None, image=None, description=None, url=None,
                 tags=None, identifiers=None, references=None, authors=None, license=None,
                 format=None, docker_hub_image_id=None, algorithms=None, created=None, updated=None):
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
            docker_hub_image_id (:obj:`str`, optional): id for image in DockerHub (e.g., "crbm/biosimulations_tellurium:2.4.1")
            algorithms (:obj:`list` of :obj:`Algorithm`, optional): supported algorithms
            created (:obj:`datetime.datetime`, optional): date that the simulator was created
            updated (:obj:`datetime.datetime`, optional): date that the simulator was last updated
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
        self.created = created
        self.updated = updated

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
            and sorted(self.algorithms, key=Algorithm.sort_key) == sorted(other.algorithms, key=Algorithm.sort_key) \
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
            'created': self.created.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created else None,
            'updated': self.updated.strftime('%Y-%m-%dT%H:%M:%SZ') if self.updated else None,
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
            created=dateutil.parser.parse(val.get('created')) if val.get('created', None) else None,
            updated=dateutil.parser.parse(val.get('updated')) if val.get('updated', None) else None,
        )
