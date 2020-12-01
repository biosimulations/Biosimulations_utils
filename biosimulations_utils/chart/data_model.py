""" Data model for chart types

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import PrimaryResource, PrimaryResourceMetadata, RemoteFile, ResourceMetadata, User
import enum

__all__ = [
    'Chart', 'ChartDataField', 'ChartDataFieldShape', 'ChartDataFieldType',
]


class Chart(PrimaryResource):
    """ Chart type

    Attributes:
        id (:obj:`str`): id
    """

    TYPE = 'chart'

    def __init__(self, id=None, metadata=None, _metadata=None):
        """
        Args:
            id (:obj:`str`, optional): id
            metadata (:obj:`PrimaryResourceMetadata`, optional): public metadata
            _metadata (:obj:`ResourceMetadata`, optional): private metadata
        """
        self.id = id
        self.metadata = metadata or PrimaryResourceMetadata()
        self._metadata = _metadata or ResourceMetadata()

    def __eq__(self, other):
        """ Determine if two chart types are semantically equal

        Args:
            other (:obj:`Chart`): other chart type

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
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
                    'metadata': self.metadata.to_json() if self.metadata else None,
                },
                'relationships': {
                    'owner': None,
                    'image': None,
                    'parent': None,
                },
                'meta': self._metadata.to_json() if self._metadata else None,
            },
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
        """ Create chart type from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Chart`
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
            metadata=PrimaryResourceMetadata.from_json(attrs.get('metadata')) if attrs.get('metadata', None) else None,
            _metadata=ResourceMetadata.from_json(data.get('meta')) if data.get('meta', None) else None,
        )

        if rel.get('owner', None):
            obj.metadata.owner = User.from_json(rel.get('owner'))
        if rel.get('image', None):
            obj.metadata.image = RemoteFile.from_json(rel.get('image'))
        if rel.get('parent', None):
            obj.metadata.parent = Chart.from_json(rel.get('parent'))

        return obj


class ChartDataField(object):
    """ Chart type data field

    Attributes:
        name (:obj:`str`): name
        shape (:obj:`ChartDataFieldShape`): shape
        type (:obj:`ChartDataFieldType`): type
    """

    def __init__(self, name=None, shape=None, type=None):
        """
        Args:
            name (:obj:`str`, optional): name
            shape (:obj:`ChartDataFieldShape`, optional): shape
            type (:obj:`ChartDataFieldType`, optional): type
        """
        self.name = name
        self.shape = shape
        self.type = type

    def __eq__(self, other):
        """ Determine if two chart types are semantically equal

        Args:
            other (:obj:`Chart`): other chart type

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.name == other.name \
            and self.shape == other.shape \
            and self.type == other.type

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'name': self.name,
            'shape': self.shape.value,
            'type': self.type.value,
        }

    @classmethod
    def from_json(cls, val):
        """ Create chart type data field from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`ChartDataField`
        """
        return cls(
            name=val.get('name', None),
            shape=ChartDataFieldShape(val.get('shape')) if val.get('shape', None) else None,
            type=ChartDataFieldType(val.get('type')) if val.get('type', None) else None,
        )

    @staticmethod
    def sort_key(field):
        """ Get a key to sort a field

        Args:
            field (:obj:`ChartDataField`): field

        Returns:
            :obj:`tuple`
        """
        return (field.name, field.shape.value if field.shape else None, field.type.value if field.type else None)


class ChartDataFieldShape(str, enum.Enum):
    """ Chart type data field shape """
    scalar = 'scalar'
    array = 'array'


class ChartDataFieldType(str, enum.Enum):
    """ Chart type data field type """
    dynamic_simulation_result = 'dynamicSimulationResult'
    static = 'static'
