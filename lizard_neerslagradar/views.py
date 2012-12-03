import logging

from django.http import HttpResponse
from django.views.generic.base import View
from django.utils import simplejson as json

import dateutil
import mapnik

import lizard_map.views
from lizard_map.models import WorkspaceEdit
from lizard_map import coordinates
from lizard_ui.layout import Action
from lizard_neerslagradar import netcdf
from lizard_neerslagradar import models

logger = logging.getLogger(__name__)


MAP_BASE_LAYER = 'map_base_layer'  # The selected base layer


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
        return (
            '148076.83040199202, 6416328.309563829, '
            '1000954.7013451669, 7223311.813260503')

    def user_logged_in(self):
        return str(self.request.user.is_authenticated())

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
            'BBOX',
            '151345.64262053, 6358643.0784661, '
            '981757.51779509, 7136466.2781877')
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
        mapnik_map = mapnik.Map(width, height)

        # Setup coordinate system and background
        mapnik_map.srs = netcdf.GOOGLEMERCATOR.ExportToProj4()
        mapnik_map.background = mapnik.Color('transparent')

        # Create a layer from the geotiff
        raster = mapnik.Gdal(file=str(path), shared=True)
        layer = mapnik.Layer(
            'Tiff Layer', netcdf.GOOGLEMERCATOR.ExportToProj4())
        layer.datasource = raster
        s = mapnik.Style()
        r = mapnik.Rule()
        rs = mapnik.RasterSymbolizer()
        rs.opacity = opacity
        r.symbols.append(rs)
        s.rules.append(r)
        layer.styles.append('geotiff')

        # Add the layer
        mapnik_map.layers.append(layer)
        mapnik_map.append_style('geotiff', s)

        # Zoom to bbox and create the PNG image
        mapnik_map.zoom_to_box(mapnik.Envelope(*bbox))
        img = mapnik.Image(width, height)
        mapnik.render(mapnik_map, img)
        img_data = img.tostring('png')

        # Return the HttpResponse
        response = HttpResponse(img_data, content_type='image/png')
        return response
