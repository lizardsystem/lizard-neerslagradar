import logging

from django.http import HttpResponse
from django.views.generic.base import View
from django.utils import simplejson as json

import dateutil

import lizard_map.views
import lizard_map.coordinates
from lizard_map.models import WorkspaceEdit
from lizard_ui.layout import Action
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


class NeerslagRadarView(lizard_map.views.AppView):
    def start_extent(self):
        # Hack: we need to have a session right away for toggling ws items.
        self.request.session[
            'make_sure_session_is_initialized'] = 'hurray'
        # End of the hack.

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


class DefaultView(NeerslagRadarView):
    template_name = 'lizard_neerslagradar/wms_neerslagradar.html'

    def dispatch(self, request, *args, **kwargs):
        """Add in the omnipresent workspace item, then proceed as normal."""

        workspace_edit = WorkspaceEdit.get_or_create(
            request.session.session_key, request.user)

        workspace_edit.add_workspace_item(
            "Neerslagradar", "adapter_neerslagradar", "{}")

        return super(DefaultView, self).dispatch(request, *args, **kwargs)

    def bbox(self):
        return TIFF_BBOX

    def user_logged_in(self):
        return self.request.user.is_authenticated()

    def region_bbox(self):
        extent = models.Region.extent_for_user(self.request.user)
        if extent:
            logger.debug(str(extent))
            bbox = ', '.join((extent['left'], extent['top'],
                              extent['right'], extent['bottom']))
            logger.debug("BBOX: {0}".format(bbox))
            return bbox

    def start_dt(self):
        return '2011-01-07T00:00:00.000Z'

    @property
    def breadcrumbs(self):
        return [Action(name='Neerslagradar', url='/')]


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
            'TIME', '2011-01-07T00:00:00.000Z/2011-01-08T00:00:00.000Z')
        times = times.split('/')
        if len(times) == 1:
            time_from = dateutil.parser.parse(times[0])
#            time_to = None
        elif len(times) == 2:
            time_from = dateutil.parser.parse(times[0])
#            time_to = dateutil.parser.parse(times[1])
        else:
            raise Exception('No time provided')

        path = netcdf.time_2_path(time_from)
        return self.serve_geotiff(path, width, height, bbox, srs, opacity)

    def serve_geotiff(self, path, width, height, bbox, srs, opacity):
        # Create a map
        png = reproject.reprojected_image(
            geotiff_path=path, width=width, height=height, bbox=bbox,
            srs=srs)

        # Return the HttpResponse
        response = HttpResponse(
            open(png, "rb").read(), content_type='image/png')
        return response
