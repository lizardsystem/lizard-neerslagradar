"""The Neerslagradar adapter. It's a bit different in that there is
only one map layer (the map layer that represents all our data) and it
is assumed that that layer is always in the workspace whenever this
app is used. So we don't really need to work with identifiers and
workspace acceptables and so on.

The most important part is the graph functionality: when a user clicks
somewhere, if he has access to that square of the map, a time series
graph pops up."""

import datetime
import logging
import urllib2
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import simplejson as json
from lizard_datasource import datasource
from lizard_map import coordinates
from lizard_map import workspace
from lizard_map.adapter import Graph, FlotGraph
from lizard_map.daterange import current_start_end_dates
from lizard_map.models import Setting
from lizard_rainapp.calculations import UNIT_TO_TIMEDELTA
from lizard_rainapp.calculations import rain_stats
from lizard_rainapp.calculations import t_to_string
from nens_graph.rainapp import RainappGraph
import mapnik
import pytz

from lizard_neerslagradar import dates
from lizard_neerslagradar import models
from lizard_neerslagradar import projections


# Hardcoded nodatavalue for precipitation
NODATAVALUE = -9999

logger = logging.getLogger(__name__)


def get_datasource():
    """Return the datasource used for the timeseries."""
    # The choices made are defined as a lizard-map setting.
    choices_made_json = Setting.get("neerslagradar_datasource")

    # Get the datasource
    return datasource.datasource(
        datasource.ChoicesMade(json=choices_made_json))


class NeerslagRadarAdapter(workspace.WorkspaceItemAdapter):
    """Registered as adapter_neerslagradar"""

    def _grid_name(self, region_name, pixel):
        """Returns name as a utf8-encoded byte string."""
        # return (u'{0}, cel ({1} {2})'
        #         .format(region_name, *pixel).encode('utf8'))
        return u"Neerslag in %s" % region_name

    def _user(self):
        """Finds the current user, or returns the AnonymousUser if not
        found."""
        if 'userid' in self.layer_arguments:
            try:
                return User.objects.get(pk=self.layer_arguments['userid'])
            except User.DoesNotExist:
                pass
        return AnonymousUser()

    def _user_has_access(self, google_x, google_y):
        """Gets the current user's extent and checks if the
        coordinates are inside the rectangle."""

        extent = models.Region.extent_for_user(self._user())
        return (
            extent and
            (float(extent['left']) <= google_x <= float(extent['right'])) and
            (float(extent['bottom']) <= google_y <= float(extent['top'])))

    def search(self, google_x, google_y, radius=None):
        if not self._user_has_access(google_x, google_y):
            return []

        lon, lat = coordinates.google_to_wgs84(google_x, google_y)
        rd_x, rd_y = coordinates.google_to_rd(google_x, google_y)

        region = models.Region.find_by_point((lon, lat), user=self._user())
        pixel = projections.coordinate_to_composite_pixel(lon, lat)

        if region is None or pixel is None:
            logger.debug("Region is None or pixel is None.")
            return []

        name = self._grid_name(region.name, pixel)

        return [{
            'distance': 0,
            'name': name,
            'shortname': name,
            'workspace_item': self.workspace_item,
            'identifier': {
                'identifier': pixel,
                'region_name': region.name,
                'google_coords': (google_x, google_y),
            },
            'google_coords': (google_x, google_y),
            'object': None
        }]

    def layer(self, layer_ids=None, webcolor=None, request=None):
        """Draw the user's region(s)."""
        user = self._user()
        if not user.is_authenticated():
            return [], {}

        query = str("""
           (SELECT
                1 AS value,
                region.geometry AS geometry
            FROM
                lizard_neerslagradar_region region
            INNER JOIN
                lizard_neerslagradar_region_users regionusers
            ON
                region.id = regionusers.region_id
            WHERE
                regionusers.user_id = {userid}
            ) AS data
            """.format(userid=user.id))

        style = mapnik.Style()
        rule = mapnik.Rule()
        inside = mapnik.PolygonSymbolizer(mapnik.Color("#0000bb"))
        inside.fill_opacity = 0.15
        # rule.symbols.append(inside)
        outside = mapnik.LineSymbolizer(mapnik.Color("#0000bb"), 2)
        outside.fill_opacity = 1
        rule.symbols.append(outside)
        style.rules.append(rule)

        default_database = settings.DATABASES['default']
        data_source = mapnik.PostGIS(
            host=default_database['HOST'],
            user=default_database['USER'],
            password=default_database['PASSWORD'],
            dbname=default_database['NAME'],
            table=query,
            geometry_field='geometry',
        )
        layer = mapnik.Layer("Gemeenten", coordinates.WGS84)
        layer.datasource = data_source

        layer.styles.append('neerslagstyle')

        return [layer], {'neerslagstyle': style}

    def location(self, identifier, region_name, layout=None):
        name = self._grid_name(region_name, identifier)

        return {
            'name': name,
            'identifier': identifier,
        }

    def image(self, identifiers=None, start_date=None, end_date=None,
              width=None, height=None, layout_extra=None):
        return self._render_graph(
            identifiers, start_date, end_date, layout_extra=layout_extra,
            GraphClass=RainappGraph)

    def flot_graph_data(
        self, identifiers, start_date, end_date, layout_extra=None,
        raise_404_if_empty=False
    ):
        return self._render_graph(
            identifiers, start_date, end_date, layout_extra=layout_extra,
            raise_404_if_empty=raise_404_if_empty,
            GraphClass=FlotGraph)

    def _render_graph(
        self, identifiers, start_date, end_date, layout_extra=None,
        raise_404_if_empty=False, GraphClass=Graph, **extra_params):
        """
        Visualize timeseries in a graph.

        Legend is always drawn.

        New: this is now a more generalized version of image(), to
        support FlotGraph.
        """

        tz = pytz.timezone(settings.TIME_ZONE)
        today_site_tz = tz.localize(datetime.datetime.now())

        start_date_utc = dates.to_utc(start_date)
        end_date_utc = dates.to_utc(end_date)
        graph = GraphClass(start_date_utc,
                           end_date_utc,
                           today=today_site_tz,
                           tz=tz,
                           **extra_params)

        # Gets timeseries, draws the bars, sets  the legend
        for identifier in identifiers:
            location_name = self._grid_name(
                identifier['region_name'], identifier['identifier'])

            cached_value_result = self.values(identifier,
                                              start_date_utc,
                                              end_date_utc)

            dates_utc_timezoneaware = [row['datetime']
                                       for row in cached_value_result]
            values = [row['value'] for row in cached_value_result]
            units = [row['unit'] for row in cached_value_result]

            unit = ''
            if len(units) > 0:
                unit = units[0]
            if values:
                unit_timedelta = UNIT_TO_TIMEDELTA.get(unit, None)
                if unit_timedelta:
                    # We can draw bars corresponding to period
                    bar_width = graph.get_bar_width(unit_timedelta)
                    offset = -1 * unit_timedelta
                    offset_dates = [d + offset
                                    for d in dates_utc_timezoneaware]
                else:
                    # We can only draw spikes.
                    bar_width = 0
                    offset_dates = dates_utc_timezoneaware
                graph.axes.bar(offset_dates,
                               values,
                               edgecolor='blue',
                               width=bar_width,
                               label=location_name)
            graph.set_ylabel(unit)
            # graph.legend()
            graph.suptitle(location_name)

            # Use first identifier and breaks the loop
            break

        graph.responseobject = HttpResponse(content_type='image/png')

        return graph.render()

    def values(self, identifier, start_date, end_date):
        # get coordinates for rasterstorequery
        cell_x, cell_y = identifier['google_coords']
        # transform datetimes for rasterstorequery
        format_ = "%Y-%m-%dT%H:%M:%SZ"
        end_date_str = datetime.datetime.strftime(end_date, format_)
        start_date_str = datetime.datetime.strftime(start_date, format_)
        # rasterstore query
        url_template = ('https://raster.lizard.net/data?request=getdata&geom='
               'POINT({x}+{y})&layer=radar:5min&sr=EPSG:3857&start={start}&'
               'stop={stop}&time=1&indent=2')
        url = url_template.format(x=cell_x, y=cell_y, start=start_date_str,
                   stop=end_date_str)
        url_file = urllib2.urlopen(url)
        rasterstore_values = json.load(url_file)

        # transform rasterstore values into required datastructure with dicts
        # in some cases rasterstore contains None values, these are set to 0
        rain_data = rasterstore_values['values']
        rain_datetimes = rasterstore_values['time']
        values = [self._rain_dict(rain_datetimes[i], val if val else 0)
                  for i, val in enumerate(rain_data)]
        return values

    def _rain_dict(self, time, value, unit=u"mm/5min"):
        """
        Return dictionary for each datapoint with datetime, value and unit
        information.

        time is a string of the format 2015-01-10T01:01:00
        """
        dtformat= '%Y-%m-%dT%H:%M:%S'
        dt = pytz.timezone('Europe/Amsterdam')\
                 .localize(datetime.datetime.strptime(time, dtformat))
        rainvalue = {'value': value, 'unit': unit,
                     'datetime': dt}
        return rainvalue

    def html(self, identifiers=None, layout_options=None):
        """
        Popup with graph - table - bargraph.

        We're using the template of RainApp's popup, so this function was
        written to result in exactly the same context variables as RainApp's
        adapter results in.
        """
        add_snippet = layout_options.get('add_snippet', False)

        # Make table with given identifiers.
        # Layer options contain request - not the best way but it works.
        start_date, end_date = current_start_end_dates(
            layout_options['request'])

        # Convert start and end dates to utc.
        start_date_utc = dates.to_utc(start_date)
        end_date_utc = dates.to_utc(end_date)

        info = []

        symbol_url = self.symbol_url()

        for identifier in identifiers:
            logger.debug("IN HTML, identifier = {0}".format(identifier))
            image_graph_url = self.workspace_mixin_item.url(
                "lizard_map_adapter_image", (identifier,))
            flot_graph_data_url = self.workspace_mixin_item.url(
                "lizard_map_adapter_flot_graph_data", (identifier,))

            values = self.values(identifier, start_date_utc, end_date_utc)
            infoname = self._grid_name(
                identifier['region_name'], identifier['identifier'])

            info.append({
                'identifier': identifier,
                'identifier_json': json.dumps(identifier).replace('"', '%22'),
                'shortname': infoname,
                'name': infoname,
                'location': infoname,
                'image_graph_url': image_graph_url,
                'flot_graph_data_url': flot_graph_data_url,
                'url': self.workspace_mixin_item.url(
                        "lizard_map_adapter_values", [identifier, ],
                        extra_kwargs={'output_type': 'csv'}),
                'workspace_item': self.workspace_mixin_item,
                'adapter': self
            })

        return render_to_string(
            'lizard_rainapp/popup_rainapp.html',
            {
                'title': infoname,
                'symbol_url': symbol_url,
                'add_snippet': add_snippet,
                'workspace_item': self.workspace_item,
                'info': info
            }
        )
