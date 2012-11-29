from django.contrib.gis.geos import GEOSGeometry
from lizard_neerslagradar import models
from lizard_map import coordinates
from osgeo import osr

# Create a RD to WGS84 transformation. Internally we store everything
# as WGS84, but the shapefile contains RD.
srrd = osr.SpatialReference()
srrd.ImportFromProj4(coordinates.RD)

srwgs84 = osr.SpatialReference()
srwgs84.ImportFromProj4(coordinates.WGS84)

rd_to_wgs84 = osr.CoordinateTransformation(srrd, srwgs84)


def import_regions_from_shapefile(shapefile):
    layer = shapefile.GetLayer()

    for feature in layer:
        name = feature.GetField('NAME')

        try:
            region = models.Region.objects.get(name=name)
            print("{0} updated.".format(name))
        except models.Region.DoesNotExist:
            region = models.Region(name=name)
            print("{0} created.".format(name))
        geometry = feature.geometry()
        geometry.Transform(rd_to_wgs84)

        region.geometry = GEOSGeometry(
            geometry.ExportToWkt())

        print(region.geometry.geom_type)
        region.save()
