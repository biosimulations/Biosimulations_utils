""" Data model for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Format, Resource, ResourceMetadata
from ..simulation.data_model import Algorithm

__all__ = ['Simulator']


class Simulator(Resource):
    """ A simulator

    Attributes:
        id (:obj:`str`): id
        version (:obj:`str`): version
        url (:obj:`str`): URL
        format (:obj:`Format`): format
        docker_hub_image_id (:obj:`str`): id for image in DockerHub (e.g., "crbm/biosimulations_tellurium:2.4.1")
        algorithms (:obj:`list` of :obj:`Algorithm`): supported algorithms
        metadata (:obj:`ResourceMetadata`): metadata
    """
    TYPE = 'simulator'

    def __init__(self, id=None, version=None, url=None,
                 format=None, docker_hub_image_id=None, algorithms=None, metadata=None):
        """
        Args:
            id (:obj:`str`, optional): id
            version (:obj:`str`, optional): version
            url (:obj:`str`, optional): URL
            format (:obj:`Format`, optional): format
            docker_hub_image_id (:obj:`str`, optional): id for image in DockerHub (e.g., "crbm/biosimulations_tellurium:2.4.1")
            algorithms (:obj:`list` of :obj:`Algorithm`, optional): supported algorithms
            metadata (:obj:`ResourceMetadata`, optional): metadata
        """
        self.id = id
        self.version = version
        self.url = url
        self.format = format
        self.docker_hub_image_id = docker_hub_image_id
        self.algorithms = algorithms or []
        self.metadata = metadata or ResourceMetadata()

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
            and self.docker_hub_image_id == other.docker_hub_image_id \
            and sorted(self.algorithms, key=Algorithm.sort_key) == sorted(other.algorithms, key=Algorithm.sort_key) \
            and self.metadata == other.metadata

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
                    'version': self.version,
                    'url': self.url,
                    'format': self.format.to_json() if self.format else None,
                    'dockerHubImageId': self.docker_hub_image_id,
                    'algorithms': [alg.to_json() for alg in self.algorithms],
                    'metadata': self.metadata.to_json() if self.metadata else None,
                },
            }
        }

    @classmethod
    def from_json(cls, val):
        """ Create simulator from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Simulation`
        """
        data = val.get('data', {})
        if data.get('type', None) != cls.TYPE:
            raise ValueError("`type` '{}' != '{}'".format(data.get('type', ''), cls.TYPE))

        attrs = data.get('attributes', {})
        return cls(
            id=data.get('id', None),
            version=attrs.get('version', None),
            url=attrs.get('url', None),
            format=Format.from_json(attrs.get('format')) if attrs.get('format', None) else None,
            docker_hub_image_id=attrs.get('dockerHubImageId', None),
            algorithms=[Algorithm.from_json(alg) for alg in attrs.get('algorithms', [])],
            metadata=ResourceMetadata.from_json(attrs.get('metadata')) if attrs.get('metadata', None) else None,
        )
