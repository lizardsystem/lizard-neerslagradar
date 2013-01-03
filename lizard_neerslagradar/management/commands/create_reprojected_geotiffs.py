from django.core.management.base import BaseCommand

from lizard_neerslagradar import scripts


class Command(BaseCommand):
    args = ""
    help = """Creating reprojected images is too slow to do on the fly, so they
can be generated using this script.

The images generated are all 512x512, and all Google
projections. Images are generated for each 5-minute step in the last
24 hours, both for the entire radar extent and for all users' extents.

This results in a lot of files. Another script should run to clean up
the files afterwards.
"""

    def handle(self, *args, **options):
        scripts.create_projected_geotiffs(stdout=self.stdout)
