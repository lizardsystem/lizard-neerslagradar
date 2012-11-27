from optparse import make_option
from optparse import OptionParser
import logging
#import os
#import sys
import contextlib
#import hashlib
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
#from django.db.models import Q

import dateutil
import netCDF4

from lizard_neerslagradar import netcdf

logger = logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ""
    help = "Create a geotiff per timestep from the radar.nc file."

    option_list = BaseCommand.option_list + (
        make_option(
            "--from", action="store", type="string",
            dest="from_", default="2011-01-07",
            help="Generate geotiffs starting from this datetime. "
            "Use a string in the format YYYY-MM-DD HH:MM "
            "(fuzzy substrings are allowed)"),
        make_option("--skip-existing", action="store_true",
                    dest="skip_existing", default=False,
                    help="Skip existing geotiffs"),
        )

    def handle(self, *args, **options):
        parser = OptionParser(option_list=self.option_list)
        (options, args) = parser.parse_args()
        logger.warn("IGNORED from=%s", options.from_)
        logger.warn("IGNORED skip_existing=%s", options.skip_existing)

        time_from = dateutil.parser.parse('2011-01-07T00:00:00.000Z')
        time_to = dateutil.parser.parse('2011-01-08T00:00:00.000Z')
        times_list = [time_from]
        if time_to:
            interval = datetime.timedelta(minutes=5)
            time = time_from
            while time < time_to:
                time += interval
                times_list.append(time)
        nc = netCDF4.Dataset(settings.RADAR_NC_PATH, 'r')
        with contextlib.closing(nc):
            for time in times_list:
                try:
                    path = netcdf.time_2_path(time)
                    netcdf.mk_geotiff(nc, time, path)
                    logger.info('Created geotiff for {}'.format(time))
                except:
                    logger.exception(
                        'While creating geotiff for {}'.format(time))
