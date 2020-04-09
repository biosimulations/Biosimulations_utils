""" Data model for visualizations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..chart_type.data_model import ChartType, ChartTypeDataField
from ..data_model import Format, Identifier, JournalReference, License, Person, RemoteFile
from ..simulation.data_model import SimulationResult

__all__ = [
    'Visualization', 'VisualizationLayoutElement', 'VisualizationDataField',
]


class Visualization(object):
    """ Visualization of the results of one or more simulations

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        image (:obj:`RemoteFile`): image file
        description (:obj:`str`): description
        tags (:obj:`list` of :obj:`str`): tags
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        references (:obj:`list` of :obj:`JournalReference`): references
        authors (:obj:`list` of :obj:`Person`): authors
        license (:obj:`License`): license
        format (:obj:`Format`): format
        columns (:obj:`int`): number of columns
        layout (:obj:`list` of :obj:`VisualizationLayoutElement`): element of the visualization
            (i.e. the cells in the grid of visualizations)
    """

    def __init__(self, id=None, name=None, image=None, description=None,
                 tags=None, identifiers=None, references=None, authors=None, license=None, format=None,
                 columns=None, layout=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            image (:obj:`RemoteFile`, optional): image file
            description (:obj:`str`, optional): description
            tags (:obj:`list` of :obj:`str`, optional): tags
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            references (:obj:`list` of :obj:`JournalReference`, optional): references
            authors (:obj:`list` of :obj:`Person`, optional): authors
            license (:obj:`License`, optional): license
            format (:obj:`Format`, optional): format
            columns (:obj:`int`, optional): number of columns
            layout (:obj:`list` of :obj:`VisualizationLayoutElement`, optional): element of the visualization
                (i.e. the cells in the grid of visualizations)
        """
        self.id = id
        self.name = name
        self.image = image
        self.description = description
        self.tags = tags or []
        self.identifiers = identifiers or []
        self.references = references or []
        self.authors = authors or []
        self.license = license
        self.format = format
        self.columns = columns
        self.layout = layout or []

    def __eq__(self, other):
        """ Determine if two simulations are semantically equal

        Args:
            other (:obj:`Simulation`): other simulation

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and self.image == other.image \
            and self.description == other.description \
            and sorted(self.tags) == sorted(other.tags) \
            and sorted(self.identifiers, key=Identifier.sort_key) == sorted(other.identifiers, key=Identifier.sort_key) \
            and sorted(self.references, key=JournalReference.sort_key) == sorted(other.references, key=JournalReference.sort_key) \
            and sorted(self.authors, key=Person.sort_key) == sorted(other.authors, key=Person.sort_key) \
            and self.license == other.license \
            and self.format == other.format \
            and self.columns == other.columns \
            and sorted(self.layout, key=VisualizationLayoutElement.sort_key) == \
            sorted(other.layout, key=VisualizationLayoutElement.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'id': self.id,
            'name': self.name,
            'image': self.image.to_json() if self.image else None,
            'description': self.description,
            'tags': self.tags or [],
            'identifiers': [identifier.to_json() for identifier in self.identifiers],
            'references': [ref.to_json() for ref in self.references],
            'authors': [author.to_json() for author in self.authors],
            'license': self.license.value if self.license else None,
            'format': self.format.to_json() if self.format else None,
            'columns': self.columns,
            'layout': [el.to_json() for el in self.layout],
        }

    @classmethod
    def from_json(cls, val):
        """ Create simulation from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`Simulation`
        """
        return cls(
            id=val.get('id', None),
            name=val.get('name', None),
            image=RemoteFile.from_json(val.get('image')) if val.get('image', None) else None,
            description=val.get('description', None),
            tags=val.get('tags', []),
            identifiers=[Identifier.from_json(identifier) for identifier in val.get('identifiers', [])],
            references=[JournalReference.from_json(ref) for ref in val.get('references', [])],
            authors=[Person.from_json(author) for author in val.get('authors', [])],
            license=License(val.get('license')) if val.get('license', None) else None,
            format=Format.from_json(val.get('format')) if val.get('format', None) else None,
            columns=val.get('columns', None),
            layout=[VisualizationLayoutElement.from_json(el) for el in val.get('layout', [])],
        )


class VisualizationLayoutElement(object):
    """ Element of a visualization (i.e. a cell in a grid of visualizations)

    Attributes:
        chart_type (:obj:`ChartType`): chart type
        data (:obj:`list` of :obj:`VisualizationDataField`): data to paint chart type
    """

    def __init__(self, chart_type=None, data=None):
        """
        Args:
            chart_type (:obj:`ChartType`, optional): chart type
            data (:obj:`list` of :obj:`VisualizationDataField`, optional): data to paint chart type
        """
        self.chart_type = chart_type
        self.data = data or []

    def __eq__(self, other):
        """ Determine if two elements are semantically equal

        Args:
            other (:obj:`VisualizationLayoutElement`): other element

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.chart_type == other.chart_type \
            and sorted(self.data, key=VisualizationDataField.sort_key) == sorted(other.data, key=VisualizationDataField.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'chartType': self.chart_type.to_json() if self.chart_type else None,
            'data': [d.to_json() for d in self.data],
        }

    @classmethod
    def from_json(cls, val):
        """ Create an element from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`VisualizationLayoutElement`
        """
        return cls(
            chart_type=ChartType.from_json(val.get('chartType')) if val.get('chartType', None) else None,
            data=[VisualizationDataField.from_json(d) for d in val.get('data', [])],
        )

    @staticmethod
    def sort_key(el):
        """ Get a key to sort an element

        Args:
            el (:obj:`VisualizationLayoutElement`): element

        Returns:
            :obj:`tuple`
        """
        return (el.chart_type.id, tuple(sorted([VisualizationDataField.sort_key(d) for d in el.data])))


class VisualizationDataField(object):
    """
    Attributes:
        data_field (:obj:`ChartTypeDataField`): data field
        simulation_results (:obj:`list` of :obj:`SimulationResult`): simulation results
    """

    def __init__(self, data_field=None, simulation_results=None):
        """
        Args:
            data_field (:obj:`ChartTypeDataField`, optional): data field
            simulation_results (:obj:`list` of :obj:`SimulationResult`, optional): simulation results
        """
        self.data_field = data_field
        self.simulation_results = simulation_results or []

    def __eq__(self, other):
        """ Determine if two fields are semantically equal

        Args:
            other (:obj:`VisualizationDataField`): other field

        Returns:
            :obj:`bool`
        """
        return other.__class__ == self.__class__ \
            and self.data_field == other.data_field \
            and sorted(self.simulation_results, key=SimulationResult.sort_key) == \
            sorted(other.simulation_results, key=SimulationResult.sort_key)

    def to_json(self):
        """ Export to JSON

        Returns:
            :obj:`dict`
        """
        return {
            'dataField': self.data_field.to_json() if self.data_field else None,
            'simulationResults': [r.to_json() for r in self.simulation_results],
        }

    @classmethod
    def from_json(cls, val):
        """ Create field from JSON

        Args:
            val (:obj:`dict`)

        Returns:
            :obj:`VisualizationDataField`
        """
        return cls(
            data_field=ChartTypeDataField.from_json(val.get('dataField')) if val.get('dataField', None) else None,
            simulation_results=[SimulationResult.from_json(r) for r in val.get('simulationResults', [])],
        )

    @staticmethod
    def sort_key(field):
        """ Get a key to sort a field

        Args:
            field (:obj:`VisualizationDataField`): field

        Returns:
            :obj:`tuple`
        """
        return (
            ChartTypeDataField.sort_key(field.data_field),
            tuple(sorted([SimulationResult.sort_key(r) for r in field.simulation_results])),
        )
