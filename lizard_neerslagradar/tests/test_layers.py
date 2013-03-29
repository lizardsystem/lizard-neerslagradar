"""Tests for layers.py"""

import mock

from django.test import TestCase

from lizard_datasource import datasource
from lizard_datasource import dummy_datasource
from lizard_neerslagradar import layers


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
