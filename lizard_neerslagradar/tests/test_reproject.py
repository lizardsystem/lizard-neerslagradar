"""Tests for reproject.py."""

import mock
import os

from django.test import TestCase

from lizard_neerslagradar import reproject


class TestReprojectedImage(TestCase):
    @mock.patch('lizard_neerslagradar.reproject.cache_path',
                return_value="dummy")
    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('lizard_neerslagradar.reproject.create_reprojected_image')
    def test_cache_exists(self, mock_create, mock_exists, mock_cache_path):
        resultpath = reproject.reprojected_image(
            None, None, None, None, None)  # Shouldn't matter
        self.assertEquals(resultpath, "dummy")
        self.assertFalse(mock_create.called)

    @mock.patch('lizard_neerslagradar.reproject.cache_path',
                return_value="dummy")
    @mock.patch('os.path.exists', return_value=False)
    @mock.patch('lizard_neerslagradar.reproject.create_reprojected_image')
    def test_cache_doesnt_exist(
        self, mock_create, mock_exists, mock_cache_path):
        resultpath = reproject.reprojected_image(
            None, None, None, None, None)  # Shouldn't matter
        self.assertEquals(resultpath, "dummy")
        mock_create.assert_called_with("dummy", None, None, None, None, None)


class TestCachePath(TestCase):
    def test_name_and_directory_creation(self):
        path = reproject.cache_path(
            geotiff_path="/tmp/some_geotiff.tiff",
            srs="4382",
            bbox=(11111, 22222, 33333, 44444),
            width=100,
            height=200)

        self.assertTrue("/tmp/some_geotiff.tiff" in path)
        self.assertTrue("4382" in path)
        self.assertTrue("11111" in path)
        self.assertTrue("22222" in path)
        self.assertTrue("33333" in path)
        self.assertTrue("44444" in path)
        self.assertTrue("100" in path)
        self.assertTrue("200" in path)
        self.assertTrue(path.endswith(".png"))

        d = os.path.dirname(path)
        self.assertTrue(os.path.exists(d))
        self.assertTrue(os.path.isdir(d))

        os.rmdir(d)


class TestCreateReprojectedImage(TestCase):
    pass
