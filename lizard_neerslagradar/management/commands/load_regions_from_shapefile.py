from django.core.management.base import BaseCommand
from osgeo import ogr
import os

from lizard_neerslagradar import scripts


class Command(BaseCommand):
    args = "shapefile"

    def handle(self, *args, **options):
        if not args:
            raise ValueError("No shapefile given.")
        if not os.path.exists(args[0]):
            raise ValueError("Shapefile {0} not found.".format(args[0]))

        drv = ogr.GetDriverByName('ESRI Shapefile')
        shapefile = drv.Open(args[0])

        scripts.import_regions_from_shapefile(shapefile)
