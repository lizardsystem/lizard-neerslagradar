from django.contrib.gis import admin
from lizard_neerslagradar import models


class RegionAdmin(admin.OSMGeoAdmin):
    search_fields = ('name',)
    list_display = ('name', 'users',)


admin.site.register(models.Region, RegionAdmin)
