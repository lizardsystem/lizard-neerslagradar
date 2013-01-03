import os
import sys

from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry

from lizard_neerslagradar import models
from lizard_neerslagradar import netcdf
from lizard_neerslagradar import reproject
from lizard_neerslagradar import views

from lizard_map import coordinates
from osgeo import osr

# Create a RD to WGS84 transformation. Internally we store everything
# as WGS84, but the shapefile contains RD.
srrd = osr.SpatialReference()
srrd.ImportFromProj4(coordinates.RD)

srwgs84 = osr.SpatialReference()
srwgs84.ImportFromProj4(coordinates.WGS84)

rd_to_wgs84 = osr.CoordinateTransformation(srrd, srwgs84)


def import_regions_from_shapefile(shapefile):
    layer = shapefile.GetLayer()

    for feature in layer:
        name = feature.GetField('NAME')

        try:
            region = models.Region.objects.get(name=name)
            print("{0} updated.".format(name))
        except models.Region.DoesNotExist:
            region = models.Region(name=name)
            print("{0} created.".format(name))
        geometry = feature.geometry()
        geometry.Transform(rd_to_wgs84)

        region.geometry = GEOSGeometry(
            geometry.ExportToWkt())

        print(region.geometry.geom_type)
        region.save()


def clean_dir(path, files_to_keep, stdout=sys.stdout, verbose=False):
    """Clean unused files from the directory structure, then clean
    empty directories."""
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if full_path not in files_to_keep:
                if verbose:
                    stdout.write("Removing file {0}.\n".format(full_path))
                os.remove(full_path)

    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        if not dirnames and not filenames:
            # Directory is empty
            if verbose:
                stdout.write("Removing directory {0}.\n".format(dirpath))
            os.rmdir(dirpath)


def create_projected_geotiffs(stdout, verbose=False):
    """Creating reprojected images is too slow to do on the fly, so
    they can be generated using this script.

    The images generated are all 512x512, and all Google
    projections. Images are generated for each 5-minute step in the
    last 24 hours, both for the entire radar extent and for all users'
    extents.

    This results in a lot of files. Another script should run to clean
    up the files afterwards.
    """

    to_srs = 'EPSG:3857'

    bbox_whole = tuple(float(c) for c in views.TIFF_BBOX.split(", "))

    extents = set((bbox_whole,))

    for user in User.objects.all():
        user_extent = models.Region.extent_for_user(user)
        if user_extent is not None:
            if verbose:
                stdout.write("Adding extent for {0}.\n".format(user))
            extents.add((user_extent['left'], user_extent['bottom'],
                        user_extent['right'], user_extent['top']))

    files_to_keep = set()

    for current in views.animation_datetimes(views.utc_now()):
        if verbose:
            stdout.write(str(current) + "\n")

        path = netcdf.time_2_path(current)

        if not os.path.exists(path):
            if verbose:
                stdout.write("Skipping {0} because it doesn't exist.\n"
                             .format(path))
            continue

        for extent in extents:
            result = reproject.reprojected_image(
                path, to_srs, extent, 525, 497)
            if result is not None:
                files_to_keep.add(result)

            if verbose:
                stdout.write("Created {0}.\n".format(result))

    # Remove files we don't need to keep anymore
    if hasattr(settings, 'GEOTIFF_ANIMATION_CACHE_DIR'):
        top_dir = settings.GEOTIFF_ANIMATION_CACHE_DIR
        clean_dir(top_dir, files_to_keep, stdout, verbose)
