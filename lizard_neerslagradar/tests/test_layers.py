"""Tests for layers.py"""

import mock
import datetime
import pytz

from django.test import TestCase

from lizard_datasource import datasource
from lizard_datasource import dummy_datasource
from lizard_neerslagradar import layers
import openradar.products

class TestGetDatasource(TestCase):
    def test_returns_same_as_lizard_datasource(self):
        with mock.patch('lizard_map.models.Setting.get',
                        return_value='{"testing": "testing"}'):
            dummy = dummy_datasource.DummyDataSource()
            with mock.patch(
                'lizard_datasource.datasource.datasource',
                return_value=dummy) as ds:
                returned_ds = layers.get_datasource()

                self.assertEquals(returned_ds, dummy)
                print(ds.call_args)
                arg = ds.call_args[0][0]
                self.assertTrue(isinstance(arg, datasource.ChoicesMade))
                self.assertEquals(arg["testing"], "testing")

    def test_grid_name(self):
        adapter = layers.NeerslagRadarAdapter(None)
        self.assertEquals(adapter._grid_name('Nieuwegein', (1, 2)),
                          'Neerslag in Nieuwegein')


class TestGetGraphValues(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.identifier = {u'identifier': [224, 241], u'region_name': u'Bodegraven',
                      u'google_coords': [534142.28021942, 6821392.8476399]}
        self.start = self._transform_UTC(datetime.datetime(2015, 6, 17, 7, 24, 36))
        self.end = self._transform_UTC(datetime.datetime(2015, 6, 19, 7, 24, 36))
        self.values = layers.NeerslagRadarAdapter.values(
            self.identifier, self.start_date, self.end_date
        )
        self.old_values = self._old_values_function(
            self.identifier, self.start_date, self.end_date
        )

    def _transform_UTC(self, dt):
        return pytz.timezone('Europe/Amsterdam')\
                   .localize(dt).astimezone(pytz.utc)

    def test_values_constant_step(self):
        l = len(self.values)
        step_values = (
            self.values[i]['datetime'] - self.values[i+1]['datetime']
            for i in range(l-1)
        )
        msg = "multiple ({}) stepsizes found instead of just 1. ".format(l)
        self.assertTrue(len(set(step_values)) == 1, msg)

    def test_values_equal_to_old_method(self):
        msg = "different values found in "
        self.assertEqual(self.values, self.oldvalues, msg)

    def _old_values_function(self, identifier, start_date, end_date):
        cell_x, cell_y = identifier['identifier']
        values = openradar.products.get_values_from_opendap(
            x=cell_x,
            y=cell_y,
            start_date=start_date,
            end_date=end_date)
        return values

