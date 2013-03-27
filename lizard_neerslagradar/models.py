#import datetime

from lizard_map import coordinates
from lizard_neerslagradar import projections

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry


class Region(models.Model):
    """Users are connected to one or more Regions. They are gemeentes,
    waterschappen etc."""

    name = models.CharField(max_length=200)
    geometry = models.PolygonField(srid=4326)  # WGS84
    objects = models.GeoManager()
    users = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name

    def users_for_the_admin(self):
        return u', '.join(self.users.all().values_list('username', flat=True))

    def google_extent(self):
        xmin, ymin, xmax, ymax = self.geometry.extent
        xming, yming = coordinates.wgs84_to_google(xmin, ymin)
        xmaxg, ymaxg = coordinates.wgs84_to_google(xmax, ymax)
        return xming, yming, xmaxg, ymaxg

    @classmethod
    def extent_for_user(cls, user):
        if not user.is_authenticated():
            return None

        if user.has_perm('lizard_neerslagradar.view_entire_region'):
            # Setting these to None leads to entire extent being set below
            # Usually only superuser will have the permission
            topleft = bottomright = None
        else:
            regions = user.region_set.all()
            if not regions:
                return None

            wgs84extents = [region.geometry.extent for region in regions]

            extents = [{
                    'left': xmin,
                    'bottom': ymin,
                    'right': xmax,
                    'top': ymax
                    } for xmin, ymin, xmax, ymax in wgs84extents]

            extent = {
                'left': min(extent['left'] for extent in extents),
                'bottom': min(extent['bottom'] for extent in extents),
                'right': max(extent['right'] for extent in extents),
                'top': max(extent['top'] for extent in extents)
                }

            # Now we want to translate the topleft and bottomright to
            # grid cells, and use their topleft and bottomright as the
            # _actual_ extent, so that it will contain whole grid
            # cells.
            topleft = projections.coordinate_to_composite_pixel(
                extent['left'], extent['top'])
            bottomright = (
                projections.coordinate_to_composite_pixel(
                    extent['right'], extent['bottom']))

        if topleft is None:
            topleft = (0, 0)
        if bottomright is None:
            cells_x, cells_y = settings.COMPOSITE_CELLS
            bottomright = (cells_x - 1, cells_y - 1)

        left, top = projections.topleft_of_composite_pixel(
            *topleft, to_projection=coordinates.google_projection)
        right, bottom = projections.bottomright_of_composite_pixel(
            *bottomright, to_projection=coordinates.google_projection)

        return {
            'left': str(left),
            'bottom':  str(bottom),
            'right': str(right),
            'top': str(top)
            }

    @classmethod
    def find_by_point(cls, point):
        """Point is a (lon, lat) coordinate. If this point is in
        multiple regions, for now we just return the first. Returns
        None if none found."""

        # Suggestion by Reinout: lizard-security enables a "tread local" with
        # the request on it. You could use the possible user object on that
        # request to try and filter out that user's region and prefer that one
        # to the others?

        point_geom = GEOSGeometry('POINT({0} {1})'.format(*point), srid=4326)
        regions = cls.objects.filter(geometry__contains=point_geom)

        if regions:
            return regions[0]
        else:
            return None
