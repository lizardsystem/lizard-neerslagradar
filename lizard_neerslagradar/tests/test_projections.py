from lizard_neerslagradar import projections
from lizard_map import coordinates
coordinates  # pyflakes

import mock

from django.test import TestCase


class TestProjections(TestCase):
    @mock.patch(
        'lizard_map.coordinates.wgs84_to_rd', return_value=(150, 150))
    def test_translates_to_rd(self, patched_wgs84):
        with self.settings(
            COMPOSITE_EXTENT=(0, 200, 200, 0),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            projections.coordinate_to_composite_pixel(10, 10)
        patched_wgs84.assert_called_with(10, 10)

    @mock.patch(
        'lizard_map.coordinates.wgs84_to_rd', return_value=(150, 150))
    def test_returns_correct_cell(self, patched_wgs84):
        with self.settings(
            COMPOSITE_EXTENT=(0, 200, 200, 0),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            x, y = projections.coordinate_to_composite_pixel(10, 10)

        self.assertEquals(x, 1)
        self.assertEquals(y, 1)

    @mock.patch(
        'lizard_map.coordinates.wgs84_to_rd', return_value=(250, 150))
    def test_x_outside_grid_returns_none(self, patched_wgs84):
        with self.settings(
            COMPOSITE_EXTENT=(0, 200, 200, 0),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            result = projections.coordinate_to_composite_pixel(10, 10)
        self.assertEquals(result, None)


class TestTopleftOfCompositePixel(TestCase):
    def test_0_0(self):
        with self.settings(
            COMPOSITE_EXTENT=(100, 300, 300, 100),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            # Topleft of (0, 0) is the topleft of the whole extent
            x, y = projections.topleft_of_composite_pixel(0, 0)
            self.assertEquals(x, 100)
            self.assertEquals(y, 300)

    def test_1_1(self):
        with self.settings(
            COMPOSITE_EXTENT=(100, 300, 300, 100),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            # Topleft of (1, 1) is (200, 200)
            x, y = projections.topleft_of_composite_pixel(1, 1)
            self.assertEquals(x, 200)
            self.assertEquals(y, 200)

    def test_2_2(self):
        with self.settings(
            COMPOSITE_EXTENT=(100, 300, 300, 100),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            # (2, 2) doesn't exist, so should raise ValueError
            self.assertRaises(
                ValueError,
                lambda: projections.topleft_of_composite_pixel(2, 2))

    def test_1_2(self):
        with self.settings(
            COMPOSITE_EXTENT=(100, 300, 300, 100),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            # (1, 2) doesn't exist, so should raise ValueError
            self.assertRaises(
                ValueError,
                lambda: projections.topleft_of_composite_pixel(1, 2))


class TestBottomRightOfCompositePixel(TestCase):
    def test_0_0(self):
        with self.settings(
            COMPOSITE_EXTENT=(100, 300, 300, 100),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):

            x, y = projections.bottomright_of_composite_pixel(0, 0)
            self.assertEquals(x, 200)
            self.assertEquals(y, 200)

    def test_1_1(self):
        with self.settings(
            COMPOSITE_EXTENT=(100, 300, 300, 100),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            # Topleft of (1, 1) is (200, 200)
            x, y = projections.bottomright_of_composite_pixel(1, 1)
            self.assertEquals(x, 300)
            self.assertEquals(y, 100)

    def test_2_2(self):
        with self.settings(
            COMPOSITE_EXTENT=(100, 300, 300, 100),
            COMPOSITE_CELLSIZE=(100, 100),
            COMPOSITE_CELLS=(2, 2)):
            # (2, 2) doesn't exist, so should raise ValueError
            self.assertRaises(
                ValueError,
                lambda: projections.bottomright_of_composite_pixel(2, 2))
