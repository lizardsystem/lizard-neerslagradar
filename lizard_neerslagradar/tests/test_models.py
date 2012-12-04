import factory

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase

from lizard_neerslagradar import models

# Found by calling coordinates.rd_to_wgs84 on 150000 450000
TOREN_AMERSFOORT = (5.3143, 52.03830)
# Small area around it
AREA_AMERSFOORT = (
    'POLYGON((5.2997 52.0472, 5.3289 52.0472, 5.3289 52.0293, '
    '5.2997 52.0293, 5.2997 52.0472))')


class UserF(factory.Factory):
    FACTORY_FOR = User
    username = 'Remco'


class RegionF(factory.Factory):
    FACTORY_FOR = models.Region
    name = "Amersfoort"

    geometry = AREA_AMERSFOORT


class TestRegion(TestCase):
    def test_has_unicode(self):
        self.assertTrue(unicode(RegionF.build()))

    def test_google_extent_works(self):
        region = RegionF.build()
        left, top, right, bottom = region.google_extent()
        self.assertNotEquals(left, right)
        self.assertNotEquals(top, bottom)

    def test_extent_for_user_none_when_not_logged_in(self):
        self.assertEquals(
            None,
            models.Region.extent_for_user(AnonymousUser()))

    def test_extent_for_user_without_regions_is_none(self):
        user = UserF.create()
        self.assertEquals(
            None,
            models.Region.extent_for_user(user))

    def test_extent_returned(self):
        user = UserF.create()
        region = RegionF.create()
        region.users.add(user)

        extent = models.Region.extent_for_user(user)
        self.assertNotEquals(extent, None)
        for key in ('left', 'bottom', 'right', 'top'):
            self.assertTrue(key in extent)
            self.assertTrue(isinstance(extent[key], str))

    def test_region_returned_for_point_inside_it(self):
        # We use the polygon defined in RegionF, (2 2) is inside it
        region = RegionF.create()
        regionfound = models.Region.find_by_point(TOREN_AMERSFOORT)
        self.assertEquals(region, regionfound)

    def test_region_not_returned_for_point_outside_it(self):
        RegionF.create()
        regionfound = models.Region.find_by_point((5, 5))
        self.assertEquals(None, regionfound)
