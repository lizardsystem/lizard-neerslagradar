import os

from lizard_ui.settingshelper import setup_logging

SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))

LOGGING = setup_logging(BUILDOUT_DIR)

DEBUG = False
TEMPLATE_DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(BUILDOUT_DIR, 'test.db')
    },
}

SITE_ID = 1
TIME_ZONE = 'Europe/Amsterdam'
LANGUAGE_CODE = 'nl'
LANGUAGES = (
    ('nl', 'Nederlands'),
    ('en', 'English'),
)
INSTALLED_APPS = [
    'lizard_neerslagradar',
    'lizard_map',
    'lizard_ui',
    'lizard_security',
    'lizard_fewsjdbc',
    'lizard_datasource',
    'compressor',
    'south',
    'django_nose',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    ]
ROOT_URLCONF = 'lizard_neerslagradar.urls'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'lizard_security.middleware.SecurityMiddleware',
    'tls.TLSRequestMiddleware',
    )

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Used for django-staticfiles
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Default items.
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    )

MAP_SHOW_MULTISELECT = False
MAP_SHOW_DATE_RANGE = False

GEOTIFF_DIR = os.path.join(BUILDOUT_DIR, 'var', 'geotiff')
RADAR_NC_PATH = '/media/WORKSPACE/lizard-regenradar/radar.nc'

# Gridproperties for resulting composite
# from nens/radar config.py
# left, right, top, bottom
COMPOSITE_EXTENT = (-110000, 390000, 700000, 210000)
COMPOSITE_CELLSIZE = (1000, 1000)
COMPOSITE_CELLS = (500, 490)

try:
    # Import local settings that aren't stored in svn.
    from lizard_neerslagradar.local_testsettings import *
except ImportError:
    pass
