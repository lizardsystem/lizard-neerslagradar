import datetime
import logging
import os

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic.base import View
from lizard_map.models import WorkspaceEdit
from lizard_ui.layout import Action
import dateutil
import lizard_map.coordinates
import lizard_map.views
import pytz

from lizard_neerslagradar import netcdf
from lizard_neerslagradar import models
from lizard_neerslagradar import reproject


logger = logging.getLogger(__name__)


MAP_BASE_LAYER = 'map_base_layer'  # The selected base layer

# We have GOOGLE geotiffs, created from the RD geotiffs with gdalwarp
# A 500x490 RD tiff turns into a 525x497 Google tiff
TIFF_DIMENSIONS = (525, 497)
# And this is the bounding box that gdalinfo gives:
TIFF_BBOX = ', '.join([
    '147419.974',  # Left, minx
    '6416139.595',  # Bottom, miny
    '1001045.904',  # Right, maxx
    '7224238.809'  # Top, maxy
])

ANIMATION_STEP = 5  # Minutes
DEFAULT_ANIMATION_HOURS = 3
LOGGED_IN_ANIMATION_HOURS = 24


def utc_now():
    return pytz.UTC.localize(datetime.datetime.utcnow())


class NeerslagRadarView(lizard_map.views.AppView):
    def start_extent(self):

        extent = models.Region.extent_for_user(self.request.user)
        logger.debug("In start_extent; extent={0}".format(extent))
        if extent is None:
            extent = super(NeerslagRadarView, self).start_extent()

        return extent


def map_location_load_default(request):
    """
    Return start_extent
    """

    request.session[MAP_BASE_LAYER] = ''  # Reset selected base layer.

    extent = models.Region.extent_for_user(request.user)
    if extent:
        return HttpResponse(json.dumps({'extent': extent}))

    return lizard_map.views.map_location_load_default(request)


def animation_datetimes(hours_before_now):
    """Generator that yields all datetimes corresponding to animation
    steps in the ``hours_before_now`` hours before 'today'."""
    today = utc_now()
    start = today - datetime.timedelta(hours=hours_before_now)
    step = datetime.timedelta(minutes=ANIMATION_STEP)

    # Round the minutes
    current = datetime.datetime(
        year=start.year,
        month=start.month,
        day=start.day,
        hour=start.hour,
        minute=(start.minute // ANIMATION_STEP) * ANIMATION_STEP,
        tzinfo=start.tzinfo)

    while current < today:
        if current >= start:
            # Rounding may have put 'current' before the
            # ``hours_before_now``-hour boundary.
            yield current
        current = current + step


class DefaultView(NeerslagRadarView):
    template_name = 'lizard_neerslagradar/wms_neerslagradar.html'
    sidebar_is_collapsed = True

    def dispatch(self, request, *args, **kwargs):
        """Add in the omnipresent workspace item, then proceed as normal."""
        # Hack: we need to have a session right away.
        request.session[
            'make_sure_session_is_initialized'] = 'hurray'
        # End of the hack.
        if request.session.session_key is None:
            request.session.save()
        workspace_edit = WorkspaceEdit.get_or_create(
            request.session.session_key, request.user)

        if request.user.is_authenticated():
            layer_json = json.dumps({
                'userid': request.user.id})
        else:
            layer_json = json.dumps({})

        workspace_edit.add_workspace_item(
            "Neerslagradar", "adapter_neerslagradar", layer_json)

        return super(DefaultView, self).dispatch(request, *args, **kwargs)

    def bbox(self):
        return TIFF_BBOX

    def user_logged_in(self):
        return self.request.user.is_authenticated()

    def region_bbox(self):
        extent = models.Region.extent_for_user(self.request.user)
        if extent:
            logger.debug(str(extent))
            bbox = ', '.join((extent['left'], extent['bottom'],
                              extent['right'], extent['top']))
            logger.debug("BBOX: {0}".format(bbox))
            return bbox

    @property
    def number_of_hours(self):
        """Return number of hours we want to show the animation for."""
        if self.user_logged_in():
            return LOGGED_IN_ANIMATION_HOURS
        return DEFAULT_ANIMATION_HOURS

    def animation_datetimes(self):
        """For every date/time in the last 3 or 24 hours, we check if the data
        is available.  We need at least the "full" geotiff, and if the user is
        logged in, then possibly a geotiff for the user's region as well.

        Returned JSON is set as a variable in Javascript
        (wms_neerslagradar.html), and used in lizard_neerslagradar.js
        to load the whole animation."""

        data = []
        for dt in animation_datetimes(self.number_of_hours):
            p = netcdf.time_2_path(dt)
            p = reproject.cache_path(
                p, 'EPSG:3857', TIFF_BBOX.split(", "), 525, 497)
            logger.debug("Checking path: {0}".format(p))
            if os.path.exists(p):
                data.append({
                    # Translate the UTC datetime to the timezone
                    # in Settings
                    'datetime': (
                        dt.astimezone(pytz.timezone(settings.TIME_ZONE)).
                        strftime("%Y-%m-%dT%H:%M")),
                })
        logger.debug("Data: {0}".format(data))

        return json.dumps(data)

    @property
    def breadcrumbs(self):
        return [Action(name='Neerslagradar', url='/')]

    @property
    def content_actions(self):
        """Strip out the date range selector if we're not logged in."""
        actions = super(DefaultView, self).content_actions
        if not self.user_logged_in():
            # Strip out the date range selector.
            actions = [action for action in actions
                       if action.klass != 'popup-date-range']
        return actions


class WmsView(View):
    def get(self, request):
        # WMS standard parameters
        width = int(request.GET.get('WIDTH', '512'))
        height = int(request.GET.get('HEIGHT', '512'))
        opacity = float(request.GET.get('OPACITY', '0.6'))

        bbox = request.GET.get(
            'BBOX', TIFF_BBOX)

        bbox = tuple([float(i.strip()) for i in bbox.split(',')])
        srs = request.GET.get('SRS', 'EPSG:3857')

        # Either a time span, or a single time can be passed
        times = request.GET.get(
            'TIME', '')
        times = times.split('/')
        if len(times) == 1 and times[0]:
            time_from = dateutil.parser.parse(times[0])
        elif len(times) == 2:
            time_from = dateutil.parser.parse(times[0])
        else:
            raise Exception('No time provided')

        # Translate from the site's timezone to UTC
        # time_from is a UTC datetime, but that's incorrect, it's
        # actually in the site's timezone. So we have to turn it into
        # a naive datetime first.
        time_from = datetime.datetime(
            year=time_from.year,
            month=time_from.month,
            day=time_from.day,
            hour=time_from.hour,
            minute=time_from.minute)
        # Get the site timezone
        tz = pytz.timezone(settings.TIME_ZONE)
        # Translate to UTC
        time_from = tz.localize(time_from).astimezone(pytz.UTC)

        # Get the path for this datetime
        path = netcdf.time_2_path(time_from)

        return self.serve_geotiff(path, width, height, bbox, srs, opacity)

    def serve_geotiff(self, path, width, height, bbox, srs, opacity):
        # Create a map
        png = reproject.reprojected_image(
            geotiff_path=path, width=width, height=height, bbox=bbox,
            srs=srs, create=False)

        if png is None:
            # It didn't exist -- return 404.
            return HttpResponseNotFound(
                "Geotiff corresponding to WMS request not found.")

        # Return the HttpResponse
        response = HttpResponse(
            open(png, "rb").read(), content_type='image/png')
        return response


def search_coordinates(request,
                       workspace_storage_id=None,
                       workspace_storage_slug=None,
                       _format='popup'):
    """Return info for search popup.

    Our customization: a not-logged-in user gets a 'contact us' page.
    Override ``lizard_neerslagradar/contact_us.html`` in the site with some
    real content.
    """
    if not request.user.is_authenticated():
        # Return 'contact us' page.
        html = render_to_string('lizard_neerslagradar/contact_us.html')
        # The following is a bit hacked and depends on lizard_map.js' handling
        # of our result in its ``set_popup_content()`` function.
        return HttpResponse(json.dumps({'html': [html]}))

    return lizard_map.views.search_coordinates(
        request,
        workspace_storage_id=workspace_storage_id,
        workspace_storage_slug=workspace_storage_slug,
        _format=_format)
