"""Functions that reproject a RD geotiff to another projection and
cache the results, for use in Lizard animations."""


import os
import shlex
import subprocess
import tempfile


def reprojected_image(geotiff_path, srs, bbox, width, height):
    """Reprojects the geotiff in geotiff_path to the projection given
    with srs, takes the area given in bbox (minx, miny, maxx, maxy in
    the destination projection), and puts it in a width x height
    image. Caches the results on disk."""

    result_path = cache_path(geotiff_path, srs, bbox, width, height)

    if not os.path.exists(result_path):
        create_reprojected_image(
            result_path, geotiff_path, srs, bbox, width, height)

    return result_path


def cache_path(geotiff_path, srs, bbox, width, height):
    """Create a PNG filename based on the geotiff path and the other arguments.

    Path is of the form geotiff_path-srs/minx-miny-maxx-maxy-widthxheight.png.

    If the directory doesn't exist yet, create it.
    """
    dirname = os.path.join(
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
