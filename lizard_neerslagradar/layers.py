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
import pytz

from django.conf import settings
from django.http import Http404

from lizard_map import workspace
from lizard_map.adapter import Graph, FlotGraph

logger = logging.getLogger(__name__)


def get_timeseries(start_date, end_date):
    pass


class NeerslagRadarAdapter(workspace.WorkspaceItemAdapter):
    """Registered as adapter_neerslagradar"""

    def search(self, google_x, google_y, radius=None):
        return [{
                'distance': 0,
                'name': 'Dummy',
                'shortname': 'dmmy',
                'workspace_item': self.workspace_item,
                'identifier': {'identifier': None},
                'google_coords': (google_x, google_y),
                'object': None
                }]

    def layer(self, layer_ids=None, webcolor=None, request=None):
        """We have no layers."""
        return [], {}

    def html(self, identifiers=None, layout_options=None):
        return self.html_default(
            identifiers=identifiers,
            layout_options=layout_options)

    def location(self, identifier, layout=None):
        return {
            'name': 'Dummy',
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

        identifiers = [{}]

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

        line_styles = self.line_styles(identifiers)

        today = datetime.datetime.now()
        graph = GraphClass(start_date, end_date, today=today,
                      tz=pytz.timezone(settings.TIME_ZONE), **extra_params)
        graph.axes.grid(True)

        # Draw extra's (from fewsunblobbed)
        title = None
        y_min, y_max = None, None

        is_empty = True

        timeseries = get_timeseries(start_date, end_date)

        identifier = identifiers[0]
        if timeseries is not None:
            is_empty = False
            # Plot data if available.
            dates = timeseries.dates()
            values = timeseries.values()
            if values:
                graph.axes.plot(
                    dates, values,
                    lw=1,
                    color=line_styles[str(identifier)]['color'],
                    label="Dummy")
        # Apply custom layout parameters.
        if 'layout' in identifier:
            layout = identifier['layout']
            if "y_label" in layout:
                graph.axes.set_ylabel(layout['y_label'])
            if "x_label" in layout:
                graph.set_xlabel(layout['x_label'])
            apply_lines(identifier, values, "Dummy")

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
