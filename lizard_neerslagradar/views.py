import logging

from django.http import HttpResponse
from django.views.generic.base import View

import dateutil
import mapnik

from lizard_map.views import AppView
from lizard_ui.layout import Action
from lizard_neerslagradar import netcdf

logger = logging.getLogger(__name__)


class DefaultView(AppView):
    template_name = 'lizard_neerslagradar/wms_neerslagradar.html'
    javascript_hover_handler = ''
    javascript_click_handler = ''

    def bbox(self):
        return (
            '148076.83040199202, 6416328.309563829, '
            '1000954.7013451669, 7223311.813260503')

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
            time_to = None
        elif len(times) == 2:
            time_from = dateutil.parser.parse(times[0])
            time_to = dateutil.parser.parse(times[1])
        else:
            raise Exception('No time provided')

        path = netcdf.time_2_path(time_from)
        return self.serve_geotiff(path, width, height, bbox, srs)

    def serve_geotiff(self, path, width, height, bbox, srs):
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
