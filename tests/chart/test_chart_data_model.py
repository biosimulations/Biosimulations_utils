""" Tests of data model for chart types

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_utils.chart.data_model import Chart, ChartDataField, ChartDataFieldShape, ChartDataFieldType
import unittest


class ChartDataModelTestCase(unittest.TestCase):
    def test_Chart(self):
        chart = Chart(id='chart type 1')
        self.assertEqual(Chart.from_json(chart.to_json()), chart)

    def test_ChartDataField(self):
        field = ChartDataField(name='field 1', shape=ChartDataFieldShape.array, type=ChartDataFieldType.static)
        self.assertEqual(ChartDataField.from_json(field.to_json()), field)
        self.assertEqual(ChartDataField.sort_key(field), ('field 1', 'array', 'static'))
