from django.conf.urls.defaults import *
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
    )


if settings.DEBUG:
    # Add this also to the projects that use this application
    urlpatterns += patterns(
        '',
        (r'', include('staticfiles.urls')),
        (r'^admin/', include(admin.site.urls)),
    )
