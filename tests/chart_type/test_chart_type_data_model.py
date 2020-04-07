""" Tests of data model for chart types

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-04-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from Biosimulations_format_utils.chart_type.data_model import ChartType, ChartTypeDataField, ChartTypeDataFieldShape, ChartTypeDataFieldType
import unittest


class ChartTypeDataModelTestCase(unittest.TestCase):
    def test_ChartType(self):
        chart_type = ChartType(id='chart type 1')
        self.assertEqual(ChartType.from_json(chart_type.to_json()), chart_type)

    def test_ChartTypeDataField(self):
        field = ChartTypeDataField(name='field 1', shape=ChartTypeDataFieldShape.array, type=ChartTypeDataFieldType.static)
        self.assertEqual(ChartTypeDataField.from_json(field.to_json()), field)
        self.assertEqual(ChartTypeDataField.sort_key(field), ('field 1', 'array', 'static'))
