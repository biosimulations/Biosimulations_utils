""" Data model for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, PrimaryResource, PrimaryResourceMetadata, RemoteFile, ResourceMetadata, User
from ..simulation.data_model import Algorithm

__all__ = ['Simulator']


class Simulator(PrimaryResource):
    """ A simulator

    Attributes:
        id (:obj:`str`): id
        version (:obj:`str`): version
        url (:obj:`str`): URL
        format (:obj:`Format`): format
        image (:obj:`str`): id for image in DockerHub (e.g., "biosimulators/tellurium:2.4.1")
        algorithms (:obj:`list` of :obj:`Algorithm`): supported algorithms
    """
    TYPE = 'simulator'

    def __init__(self, id=None, version=None, url=None,
                 format=None, image=None, algorithms=None, metadata=None, _metadata=None):
        """
        Args:
            id (:obj:`str`, optional): id
            version (:obj:`str`, optional): version
            url (:obj:`str`, optional): URL
            format (:obj:`Format`, optional): format
            image (:obj:`str`, optional): id for image in DockerHub (e.g., "biosimulators/tellurium:2.4.1")
            algorithms (:obj:`list` of :obj:`Algorithm`, optional): supported algorithms
            metadata (:obj:`PrimaryResourceMetadata`, optional): public metadata
            _metadata (:obj:`ResourceMetadata`, optional): private metadata
        """
        self.id = id
        self.version = version
        self.url = url
        self.format = format
        self.image = image
        self.algorithms = algorithms or []
        self.metadata = metadata or PrimaryResourceMetadata()
        self._metadata = _metadata or ResourceMetadata()

    def __eq__(self, other):
        """ Determine if two simulators are semantically equal

        Args:
            other (:obj:`Simulator`): other simulator

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.version == other.version \
            and self.url == other.url \
            and self.format == other.format \
            and self.image == other.image \
            and sorted(self.algorithms, key=Algorithm.sort_key) == sorted(other.algorithms, key=Algorithm.sort_key) \
            and self.metadata == other.metadata \
            and self._metadata == other._metadata

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
                    'version': self.version,
                    'url': self.url,
                    'format': self.format.to_json() if self.format else None,
                    'image': self.image,
                    'algorithms': [alg.to_json() for alg in self.algorithms],
                    'metadata': self.metadata.to_json() if self.metadata else None,
                },
                'relationships': {
                    'owner': None,
                    'image': None,
                    'parent': None,
                },
                'meta': self._metadata.to_json() if self._metadata else None,
            }
        }

        if self.metadata.owner:
            json['data']['relationships']['owner'] = {
                'data': {
                    'type': self.metadata.owner.TYPE,
                    'id': self.metadata.owner.id,
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
        """ Create simulator from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Simulation`
        """
        if val is None or val.get('data', None) is None:
            return None

        data = val.get('data', {})
        if data.get('type', None) != cls.TYPE:
            raise ValueError("`type` '{}' != '{}'".format(data.get('type', ''), cls.TYPE))

        attrs = data.get('attributes', {})
        rel = data.get('relationships', {})

        obj = cls(
            id=data.get('id', None),
            version=attrs.get('version', None),
            url=attrs.get('url', None),
            format=Format.from_json(attrs.get('format')) if attrs.get('format', None) else None,
            image=attrs.get('image', None),
            algorithms=[Algorithm.from_json(alg) for alg in attrs.get('algorithms', [])],
            metadata=PrimaryResourceMetadata.from_json(attrs.get('metadata')) if attrs.get('metadata', None) else None,
            _metadata=ResourceMetadata.from_json(data.get('meta')) if data.get('meta', None) else None,
        )

        if rel.get('owner', None):
            obj.metadata.owner = User.from_json(rel.get('owner'))
        if rel.get('image', None):
            obj.metadata.image = RemoteFile.from_json(rel.get('image'))
        if rel.get('parent', None):
            obj.metadata.parent = Simulator.from_json(rel.get('parent'))

        return obj
