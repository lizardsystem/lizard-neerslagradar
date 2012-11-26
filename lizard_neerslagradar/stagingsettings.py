import os

from lizard_neerslagradar.testsettings import *

DEBUG = False
TEMPLATE_DEBUG = True
DATABASES = {
    'default': {
        'NAME': 'neerslagradar',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'USER': 'neerslagradar',
        'PASSWORD': 'Skjd7fi(476257HJsa',
        'HOST': 's-web-db-00-d03.external-nens.local',
        'PORT': '5432',
    },
}

GEOTIFF_DIR = os.path.join(BUILDOUT_DIR, 'var', 'geotiff')
RADAR_NC_PATH = os.path.join(BUILDOUT_DIR, 'var', 'netcdf', 'radar.nc')
