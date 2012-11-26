import os
import contextlib
import logging
import hashlib
import datetime

from django.conf import settings

from osgeo import osr
#from PIL import Image
import numpy as np
import netCDF4
#import dateutil
import gdal
import matplotlib
from matplotlib import cm

GOOGLEMERCATOR = osr.SpatialReference()
GOOGLEMERCATOR.ImportFromEPSG(3857)
WGS84 = osr.SpatialReference()
WGS84.ImportFromEPSG(4326)
TRANSFORM = osr.CoordinateTransformation(WGS84, GOOGLEMERCATOR)

logger = logging.getLogger(__name__)

def time_2_path(datetime):
    formatted = datetime.strftime("%Y-%m-%d-%H-%M")
    #fn = hashlib.md5(str(datetime)).hexdigest() + '.tiff'
    fn = '{}.tiff'.format(formatted)
    return os.path.join(settings.GEOTIFF_DIR, fn)

def normalize(arr, tmin=0.0, tmax=1.0):
    fmin = abs(arr.min())
    fmax = abs(arr.max())
    return tmin + (tmax - tmin) * (arr - fmin) / (fmax - fmin)

def mk_geotiff(nc, time, path):
    # radar.nc times don't seem timezone aware, so strip
    # the tzinfo
    time = time.replace(tzinfo=None)

    # find the actual data variable
    # data variable is first found that is mapped to the grid
    data_var = [v for v in nc.variables.itervalues() if hasattr(v, 'grid_mapping')]
    if not data_var:
        raise Exception('Could not determine grid mapping')
    data_var = data_var[0]
    time_var = nc.variables['time']

    ysize, xsize = data_var.shape[1:3]

    driver = gdal.GetDriverByName('GTiff')
    geotiff = driver.Create(str(path), xsize, ysize, 4, gdal.GDT_Byte)
    geotiff.SetProjection(GOOGLEMERCATOR.ExportToWkt())

    # calc geo transform
    lats = nc.variables['lat']
    lons = nc.variables['lon']
    # lat, lon = y, x
    left, top, z = TRANSFORM.TransformPoint(lons[0], lats[-1])
    right, bottom, z = TRANSFORM.TransformPoint(lons[-1], lats[0])
    logger.debug('l b r t = %s', (left, bottom, right, top))
    x_resolution = abs(right - left) / (len(lons) - 1)
    y_resolution = abs(bottom - top) / (len(lats) - 1)
    geo_transform = [
        left, # top left x
        x_resolution, # x resolution (west - east)
        0, # x rotation
        top, # top left y
        0, # y rotation
        -y_resolution # y resolution (north - south)
    ]
    geotiff.SetGeoTransform(geo_transform)

    time_idx = netCDF4.date2index(time, time_var, select='nearest')
    vals = data_var[time_idx][::-1]
    nans = vals.mask

    # create band-arrays (R,G,B,alpha)
    band1 = np.zeros([ysize, xsize], np.uint8)
    band2 = np.zeros([ysize, xsize], np.uint8)
    band3 = np.zeros([ysize, xsize], np.uint8)
    band4 = np.ones([ysize, xsize], np.uint8) * 255

    #if time.minute == 0 and time.hour == 1:
    #    import pdb; pdb.set_trace()

    normalizer = matplotlib.colors.LogNorm(vmin=0.1, vmax=30)
    normalized = normalizer(vals)
    cmapped = cm.jet(normalized, bytes=True)
    band1 = cmapped[:,:,0]
    band2 = cmapped[:,:,1]
    band3 = cmapped[:,:,2]
    band4 = cmapped[:,:,3]
    band4[nans] = 0

    geotiff.GetRasterBand(1).WriteArray(band1)
    geotiff.GetRasterBand(2).WriteArray(band2)
    geotiff.GetRasterBand(3).WriteArray(band3)
    geotiff.GetRasterBand(4).WriteArray(band4)

    geotiff.FlushCache()
