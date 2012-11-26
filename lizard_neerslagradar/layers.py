"""
Adapter for lizard-sticky
"""
import os
import logging
import mapnik

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json

from lizard_map import workspace
from lizard_map.coordinates import WGS84
from lizard_map.coordinates import wgs84_to_google
from lizard_map.models import ICON_ORIGINALS
from lizard_map.symbol_manager import SymbolManager
#from lizard_sticky.models import Sticky
#from lizard_sticky.models import Tag

'''
ICON_STYLE = {'icon': 'sticky.png',
              'mask': ('sticky_mask.png', ),
              'color': (1, 1, 0, 0)}

logger = logging.getLogger('lizard_sticky.layers')


class WorkspaceItemAdapterSticky(workspace.WorkspaceItemAdapter):

    def __init__(self, *args, **kwargs):
        """
        tags: list or queryset of tags

        If no tags are selected, all stickies are selected!
        """
        super(WorkspaceItemAdapterSticky, self).__init__(*args, **kwargs)
        self.tags = []
        self.tag_objects = []
        if 'tags' in self.layer_arguments:
            self.tags = self.layer_arguments['tags']
            self.tag_objects = [Tag.objects.get(slug=tag) for tag in self.tags]

    def style(self):
        """
        Make mapnik point style
        """
        symbol_manager = SymbolManager(
            ICON_ORIGINALS,
            os.path.join(settings.MEDIA_ROOT, 'generated_icons'))
        output_filename = symbol_manager.get_symbol_transformed(
            ICON_STYLE['icon'], **ICON_STYLE)
        output_filename_abs = os.path.join(
            settings.MEDIA_ROOT, 'generated_icons', output_filename)
        # use filename in mapnik pointsymbolizer
        point_looks = mapnik.PointSymbolizer(
            output_filename_abs, 'png', 16, 16)
        point_looks.allow_overlap = True
        layout_rule = mapnik.Rule()
        layout_rule.symbols.append(point_looks)
        point_style = mapnik.Style()
        point_style.rules.append(layout_rule)

        return point_style

    def layer(self, layer_ids=None, request=None):
        """Return a layer with all stickies or stickies with selected
        tags
        """

        # Use these coordinates to put points 'around' actual
        # coordinates, to compensate for bug #402 in mapnik.
        around = [(0.00001, 0),
                  (-0.00001, 0),
                  (0, 0.00001),
                  (0, -0.00001)]

        layers = []
        styles = {}
        layer = mapnik.Layer("Stickies", WGS84)

        layer.datasource = mapnik.PointDatasource()
        if self.tag_objects:
            stickies = Sticky.objects.filter(tags__in=self.tag_objects)
        else:
            stickies = Sticky.objects.all()

        for sticky in stickies:
            layer.datasource.add_point(
                sticky.geom.x, sticky.geom.y, 'Name', str(sticky.title))
            for offset_x, offset_y in around:
                layer.datasource.add_point(
                    sticky.geom.x + offset_x,
                    sticky.geom.y + offset_y,
                    'Name',
                    str(sticky.title))

        # generate "unique" point style name and append to layer
        style_name = "Stickies"
        styles[style_name] = self.style()
        layer.styles.append(style_name)

        layers = [layer, ]
        return layers, styles

    def values(self, identifier, start_date, end_date):
        """Return values in list of dictionaries (datetime, value, unit)
        """

        stickies = Sticky.objects.filter(datetime__gte=start_date,
                                         datetime__lte=end_date)
        return [{'datetime': sticky.datetime,
                 'value': sticky.description,
                 'unit': ''} for sticky in stickies]

    def search(self, google_x, google_y, radius=None):
        """
        returns a list of dicts with keys distance, name, shortname,
        google_coords, workspace_item, identifier
        """
        #from lizard_map.coordinates import google_to_rd
        #x, y = google_to_rd(google_x, google_y)
        #pnt = Point(x, y, srid=28992)  # 900913
        pnt = Point(google_x, google_y, srid=900913)  # 900913
        #print pnt, radius
        stickies = Sticky.objects.filter(
            geom__distance_lte=(pnt, D(m=radius * 0.5)))

        result = [{'distance': 0.0,
                   'name': '%s (%s)' % (sticky.title, sticky.reporter),
                   'shortname': str(sticky.title),
                   'object': sticky,
                   #'google_coords': wgs84_to_google(sticky.geom.x,
                   #                                 sticky.geom.y),
                   'workspace_item': self.workspace_item,
                   'identifier': {'sticky_id': sticky.id},
                   } for sticky in stickies]
        return result

    def location(self, sticky_id, layout=None):
        """
        returns location dict.

        requires identifier_json
        """
        sticky = get_object_or_404(Sticky, pk=sticky_id)
        identifier = {'sticky_id': sticky.id}
        return {
            'name': '%s (%s)' % (sticky.title, sticky.reporter),
            'shortname': str(sticky.title),
            'workspace_item': self.workspace_item,
            'identifier': identifier,
            'google_coords': wgs84_to_google(sticky.geom.x, sticky.geom.y),
            'object': sticky,
            }

    def symbol_url(self, identifier=None, start_date=None, end_date=None):
        return super(WorkspaceItemAdapterSticky, self).symbol_url(
            identifier=identifier,
            start_date=start_date,
            end_date=end_date,
            icon_style=ICON_STYLE)

    def html(self, identifiers=None, layout_options=None):
        """
        Renders stickies
        Note: removed snipper_group kwargs because it is not used anymore.
        Therefore sticky now requires lizard_map >= 3.7, the current
        version.
        """

        display_group = [
            self.location(**identifier) for identifier in identifiers]
        add_snippet = False
        if layout_options and 'add_snippet' in layout_options:
            add_snippet = layout_options['add_snippet']
        return render_to_string(
            'lizard_sticky/popup_sticky.html',
            {'display_group': display_group,
             'add_snippet': add_snippet,
             'symbol_url': self.symbol_url(),
             'adapter_class': self.adapter_class,
             'adapter_layer_json': json.dumps(self.layer_arguments)})
'''
