""" Data model for chart types

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum

__all__ = [
    'Chart', 'ChartDataField', 'ChartDataFieldShape', 'ChartDataFieldType',
]


class Chart(object):
    """ Chart type

    Attributes:
        id (:obj:`str`): id
    """

    def __init__(self, id=None):
        """
        Args:
            id (:obj:`str`, optional): id
        """
        self.id = id

    def __eq__(self, other):
        """ Determine if two chart types are semantically equal

        Args:
            other (:obj:`Chart`): other chart type

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
            'id': self.id
        }

    @classmethod
    def from_json(cls, val):
        """ Create chart type from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Chart`
        """
        return cls(
            id=val.get('id', None)
        )


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
