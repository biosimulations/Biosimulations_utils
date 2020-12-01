""" Tests of data model for chart types

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulations_utils.data_model import (Identifier, JournalCitation, License, Person,
                                             PrimaryResourceMetadata, RemoteFile, ResourceMetadata, ResourceReferences, User)
from biosimulations_utils.chart.data_model import Chart, ChartDataField, ChartDataFieldShape, ChartDataFieldType
import datetime
import dateutil
import unittest


class ChartDataModelTestCase(unittest.TestCase):
    def test_Chart(self):
        now = datetime.datetime.utcnow().replace(microsecond=0).replace(tzinfo=dateutil.tz.UTC)
        chart = Chart(
            id='chart type 1',
            metadata=PrimaryResourceMetadata(
                name='chart 1',
                image=RemoteFile(id='chart-thumbnail'),
                description='description',
                tags=['a', 'b', 'c'],
                references=ResourceReferences(
                    identifiers=[Identifier(namespace='biomodels.db', id='XXX')],
                    citations=[
                        JournalCitation(authors='John Doe and Jane Doe', title='title', journal='journal',
                                        volume=10, issue=3, pages='1-10', year=2020, doi='10.1016/XXXX'),
                    ]
                ),
                authors=[
                    Person(first_name='John', middle_name='C', last_name='Doe'),
                    Person(first_name='Jane', middle_name='D', last_name='Doe'),
                ],
                license=License.cc0,
                owner=User(id='user-id'),
                parent=Chart(id='parent-viz'),
            ),
            _metadata=ResourceMetadata(
                version=3,
                created=now,
                updated=now,
            ),
        )
        self.assertEqual(Chart.from_json(chart.to_json()), chart)

    def test_ChartDataField(self):
        field = ChartDataField(name='field 1', shape=ChartDataFieldShape.array, type=ChartDataFieldType.static)
        self.assertEqual(ChartDataField.from_json(field.to_json()), field)
        self.assertEqual(ChartDataField.sort_key(field), ('field 1', 'array', 'static'))
