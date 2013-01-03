"""Functions that reproject a RD geotiff to another projection and
cache the results, for use in Lizard animations."""

import logging
import os
import shlex
import subprocess
import tempfile

from django.conf import settings

logger = logging.getLogger(__name__)


def reprojected_image(geotiff_path, srs, bbox, width, height, create=True):
    """Reprojects the geotiff in geotiff_path to the projection given
    with srs, takes the area given in bbox (minx, miny, maxx, maxy in
    the destination projection), and puts it in a width x height
    image. Caches the results on disk."""

    result_path = cache_path(geotiff_path, srs, bbox, width, height)

    if not os.path.exists(result_path):
        if create:
            create_reprojected_image(
                result_path, geotiff_path, srs, bbox, width, height)
        else:
            return None

    return result_path


def cache_path(geotiff_path, srs, bbox, width, height):
    """Create a PNG filename based on the geotiff path and the other arguments.

    Path is of the form geotiff_path-srs/minx-miny-maxx-maxy-widthxheight.png.

    If the directory doesn't exist yet, create it.
    """

    # The srs usually has a ':' in it (like "EPSG:3857"). That
    # character isn't allowed in Windows paths, and for some reason we
    # use Windows file servers.
    srs = srs.replace(':', '_')

    if geotiff_path.startswith("/"):
        geotiff_path = geotiff_path[1:]

    dirname = os.path.join(
        getattr(settings, 'GEOTIFF_ANIMATION_CACHE_DIR', '/tmp'),
        "{0}-{1}".format(geotiff_path, srs),
        "{0}-{1}-{2}-{3}".format(*bbox))

    pathname = os.path.join(
        dirname,
        "{0}x{1}.png".format(width, height))

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    return pathname


WARP_COMMAND = ' '.join((
        "gdalwarp",
        '-t_srs {srs}',
        '-te {xmin} {ymin} {xmax} {ymax}',
        '-ts {width} {height}',
        '-r near',
        #    '-overwrite',  # Gdal 1.9+
        '-co "COMPRESS=DEFLATE"',
        '-q',
        '{input_path}',
        '{temp_path}'))

TRANSLATE_COMMAND = ' '.join((
        "gdal_translate",
        "-of png",
        "-q",
        "{temp_path}",
        "{output_path}"))


def create_reprojected_image(
    dest_path, from_path, srs_to, bbox, width, height):

    tempdir = tempfile.mkdtemp()
    tempf = os.path.join(tempdir, 'temp.tiff')
    subprocess.call(shlex.split(WARP_COMMAND.format(
                srs=srs_to,
                xmin=bbox[0], ymin=bbox[1], xmax=bbox[2], ymax=bbox[3],
                width=width, height=height, input_path=from_path,
                temp_path=tempf)))

    subprocess.call(shlex.split(TRANSLATE_COMMAND.format(
                temp_path=tempf, output_path=dest_path)))

    try:
        os.remove(dest_path + ".aux.xml")
    except OSError:
        # Apparently it didn't exist, whatever
        pass

    os.remove(tempf)
    os.rmdir(tempdir)
