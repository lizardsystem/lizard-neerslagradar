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
import pandas
from pydap import client
import pytz

from django.conf import settings
from django.http import Http404
from django.template.loader import render_to_string
from django.utils import simplejson as json

from lizard_map import coordinates
from lizard_map import workspace
from lizard_map.adapter import Graph, FlotGraph
from lizard_map.daterange import current_start_end_dates

from lizard_rainapp.calculations import t_to_string
from lizard_rainapp.calculations import rain_stats

from lizard_neerslagradar import projections
from lizard_neerslagradar import models

logger = logging.getLogger(__name__)


DATASET_URL = 'http://gmdb.lizard.net/thredds/dodsC/radar/radar.nc'

UTC = pytz.utc
UTC_2000 = UTC.localize(datetime.datetime(2000, 1, 1))


def minutes_since_2000_to_utc(minutes_since_2000):
    return UTC_2000 + datetime.timedelta(minutes=minutes_since_2000)


def utc_to_minutes_since_2000(utc_datetime):
    return int((utc_datetime - UTC_2000).total_seconds() / 60)


def to_utc(datetime_object):
    """If datetime is naive, assume it is UTC and turn it into a UTC
    date. If it has an associated timezone, translate to UTC."""

    if datetime_object.utcoffset() is None:
        return UTC.localize(datetime_object)
    else:
        return datetime_object.astimezone(UTC)


class Timeseries(object):
    """Class copied from the in-progress lizard-datasource. Should be
    imported from somewhere later."""
    def __init__(
        self,
        timeseries_dict=None,
        timeseries_pandas=None,
        timeseries_times=None, timeseries_values=None):
        """
        Can be called with either:

        timeseries_dict, a dict with UTC datetimes as keys and floats
        as values.

        timeseries_pandas, a pandas timeseries.

        timeseries_times and timeseries_values, two iterables of equal
        length containing the times (UTC datetimes) and values of the
        timeseries."""
        if timeseries_dict is not None:
            self.timeseries = pandas.Series(timeseries_dict)
        elif timeseries_pandas is not None:
            self.timeseries = timeseries_pandas.copy()
        elif timeseries_times is not None and timeseries_values is not None:
            self.timeseries = pandas.Series(
                index=timeseries_times, data=timeseries_values)
        else:
            raise ValueError("Timeseries.__init__ called incorrectly.")

    def dates(self):
        return self.timeseries.keys()

    def values(self):
        return list(self.timeseries)

    def iter_items(self):
        return ((k, self.timeseries[k]) for k in self.timeseries.keys())


def get_timeseries(start_date, end_date, identifier):
    pixel_x, pixel_y = identifier['identifier']

    start_minutes_since_2000 = utc_to_minutes_since_2000(start_date)
    end_minutes_since_2000 = utc_to_minutes_since_2000(end_date)

    dataset = client.open_url(DATASET_URL)

    selected_dates = ((dataset.time >= start_minutes_since_2000) &
                      (dataset.time <= end_minutes_since_2000))

    if not any(selected_dates):
        return None

    dates = [minutes_since_2000_to_utc(d)
             for d in dataset['time'][selected_dates]]

    series = [max(s, 0)
              for s in
              dataset['rain']['rain'][selected_dates, pixel_x, pixel_y]]

    return Timeseries(timeseries_times=dates, timeseries_values=series)


class NeerslagRadarAdapter(workspace.WorkspaceItemAdapter):
    """Registered as adapter_neerslagradar"""

    def _grid_name(self, region_name, pixel):
        """Returns name as a utf8-encoded byte string."""
        return (u'{0}, cel ({1} {2})'
                .format(region_name, *pixel).encode('utf8'))

    def search(self, google_x, google_y, radius=None):
        lon, lat = coordinates.google_to_wgs84(google_x, google_y)
        rd_x, rd_y = coordinates.google_to_rd(google_x, google_y)

        region = models.Region.find_by_point((lon, lat))
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
                    'region_name': region.name
                    },
                'google_coords': (google_x, google_y),
                'object': None
                }]

    def layer(self, layer_ids=None, webcolor=None, request=None):
        """We have no layers."""
        return [], {}

    def location(self, identifier, region_name, layout=None):
        name = self._grid_name(region_name, identifier)

        return {
            'name': name,
            'identifier': identifier,
            }

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

        logger.debug("_RENDER_GRAPH entered")
        logger.debug("identifiers: {0}".format(identifiers))

        def apply_lines(identifier, values, location_name):
            """Adds lines that are defined in layout. Uses function
            variable graph, line_styles.

            Inspired by fewsunblobbed"""

            layout = identifier['layout']

            if "line_min" in layout:
                graph.axes.axhline(
                    min(values),
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['min_linewidth'],
                    ls=line_styles[str(identifier)]['min_linestyle'],
                    label='Minimum %s' % location_name)
            if "line_max" in layout:
                graph.axes.axhline(
                    max(values),
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['max_linewidth'],
                    ls=line_styles[str(identifier)]['max_linestyle'],
                    label='Maximum %s' % location_name)
            if "line_avg" in layout and values:
                average = sum(values) / len(values)
                graph.axes.axhline(
                    average,
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['avg_linewidth'],
                    ls=line_styles[str(identifier)]['avg_linestyle'],
                    label='Gemiddelde %s' % location_name)

        logger.debug("Voor line_styles")
        line_styles = self.line_styles(identifiers)
        logger.debug("Na line_styles")

        today = datetime.datetime.now()
        graph = GraphClass(start_date, end_date, today=today,
                      tz=pytz.timezone(settings.TIME_ZONE), **extra_params)
        graph.axes.grid(True)

        # Draw extra's (from fewsunblobbed)
        title = None
        y_min, y_max = None, None

        is_empty = True

        identifier = identifiers[0]
        timeseries = get_timeseries(start_date, end_date, identifier)

        logger.debug("Voor check of timeseries None is")

        if timeseries is not None:
            is_empty = False
            # Plot data if available.
            dates = timeseries.dates()
            values = timeseries.values()

            if values:
                graph.axes.bar(
                    dates,
                    values,
                    width=graph.get_bar_width(datetime.timedelta(minutes=5)),
                    edgecolor=line_styles[str(identifier)]['color'],
                    label=identifier.get('region_name', '?'))
        # Apply custom layout parameters.
        if 'layout' in identifier:
            layout = identifier['layout']
            if "y_label" in layout:
                graph.axes.set_ylabel(layout['y_label'])
            if "x_label" in layout:
                graph.set_xlabel(layout['x_label'])
            apply_lines(identifier, values, identifier.get('region_name', '?'))

        if is_empty and raise_404_if_empty:
            raise Http404

        graph.legend()

        # If there is data, don't draw a frame around the legend
        if graph.axes.legend_ is not None:
            graph.axes.legend_.draw_frame(False)
        else:
            # TODO: If there isn't, draw a message. Give a hint that
            # using another time period might help.
            pass

        # Extra layout parameters. From lizard-fewsunblobbed.
        y_min_manual = y_min is not None
        y_max_manual = y_max is not None
        if y_min is None:
            y_min, _ = graph.axes.get_ylim()
        if y_max is None:
            _, y_max = graph.axes.get_ylim()

        if title:
            graph.suptitle(title)

        graph.set_ylim(y_min, y_max, y_min_manual, y_max_manual)

        # Copied from lizard-fewsunblobbed.
        if "horizontal_lines" in layout_extra:
            for horizontal_line in layout_extra['horizontal_lines']:
                graph.axes.axhline(
                    horizontal_line['value'],
                    ls=horizontal_line['style']['linestyle'],
                    color=horizontal_line['style']['color'],
                    lw=horizontal_line['style']['linewidth'],
                    label=horizontal_line['name'])

        graph.add_today()
        return graph.render()

    def values(self, identifier, start_date, end_date):
        # Convert start and end dates to utc.
        start_date_utc = to_utc(start_date)
        end_date_utc = to_utc(end_date)

        timeseries = get_timeseries(
            start_date_utc, end_date_utc, identifier)

        return [{
                'datetime': k,
                'value': v,
                'unit': 'mm/5min'} for (k, v) in timeseries.iter_items()]

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
        start_date_utc = to_utc(start_date)
        end_date_utc = to_utc(end_date)

        td_windows = [datetime.timedelta(days=2),
                      datetime.timedelta(days=1),
                      datetime.timedelta(hours=3),
                      datetime.timedelta(hours=1)]

        info = []

        symbol_url = self.symbol_url()

        for identifier in identifiers:
            logger.debug("IN HTML, identifier = {0}".format(identifier))
            image_graph_url = self.workspace_mixin_item.url(
                "lizard_map_adapter_image", (identifier,))
            flot_graph_data_url = self.workspace_mixin_item.url(
                "lizard_map_adapter_flot_graph_data", (identifier,))

            values = self.values(identifier, start_date_utc, end_date_utc)

            area_km2 = 1.0  # A defining feature of the Neerslagradar
                            # is that we always work in a 1km x 1km
                            # grid.

            period_summary_row = {
                'max': sum(v['value'] for v in values),
                'start': start_date,
                'end': end_date,
                'delta': (end_date - start_date).days,
                't': t_to_string(None),
            }
            infoname = self._grid_name(
                identifier['region_name'], identifier['identifier'])

            info.append({
                'identifier': identifier,
                'identifier_json': json.dumps(identifier).replace('"', '%22'),
                'shortname': infoname,
                'name': infoname,
                'location': infoname,
                'period_summary_row': period_summary_row,
                'table': [rain_stats(values,
                                     area_km2,
                                     td_window,
                                     start_date_utc,
                                     end_date_utc)
                          for td_window in td_windows],
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
