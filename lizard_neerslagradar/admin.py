from django.contrib.gis import admin
from lizard_neerslagradar import models


class RegionAdmin(admin.OSMGeoAdmin):
    search_fields = ('name',)
    list_display = ('name', 'users_for_the_admin',)


admin.site.register(models.Region, RegionAdmin)
