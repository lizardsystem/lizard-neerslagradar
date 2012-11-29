from django.contrib.gis import admin
from lizard_neerslagradar import models


admin.site.register(models.Region, admin.OSMGeoAdmin)
