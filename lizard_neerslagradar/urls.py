from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import include
from django.conf.urls.defaults import url
from django.conf import settings
from django.contrib import admin

from lizard_neerslagradar import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$',
        views.DefaultView.as_view(),
        name='lizard_neerslagradar.default'),
    url(r'^wms/$',
        views.WmsView.as_view(),
        name='lizard_neerslagradar.wms'),
    (r'^map/', include('lizard_map.urls')),
    # Overridden because we do our own thing with the zoom button
    (r'^map_location_load_default$',
     'lizard_neerslagradar.views.map_location_load_default',
     {},
     'lizard_map.map_location_load_default'),
    (r'^admin/', include(admin.site.urls)),
    )


if settings.DEBUG:
    # Add this also to the projects that use this application
    urlpatterns += patterns(
        '',
        (r'', include('staticfiles.urls')),
    )
