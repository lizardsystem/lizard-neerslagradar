from django.conf import settings

from lizard_map import coordinates


def coordinate_to_composite_pixel(lon, lat):

    """Takes a (lon, lat) coordinate and figures out in which grid
    coordinates of the composite the point falls."""

    rd_x, rd_y = coordinates.wgs84_to_rd(lon, lat)

    minx, maxx, maxy, miny = settings.COMPOSITE_EXTENT
    cellsize_x, cellsize_y = settings.COMPOSITE_CELLSIZE

    cells_y = (maxy - miny + 1) / cellsize_y

    if not (minx <= rd_x <= maxx) or not (miny <= rd_y <= maxy):
        return None

    x = int((rd_x - minx) / cellsize_x)
    y = int(cells_y - ((rd_y - miny) / cellsize_y))

    return (x, y)


def topleft_of_composite_pixel(x, y, to_projection=coordinates.rd_projection):
    """To_projection is e.g. coordinates.google_projection."""
    left, right, top, bottom = settings.COMPOSITE_EXTENT
    dx, dy = settings.COMPOSITE_CELLSIZE

    dy = -dy  # Because top > bottom

    topleft_x = left + x * dx
    topleft_y = top + y * dy

    if topleft_x > right - 1:
        raise ValueError("x not in bounds")
    if topleft_y - 1 < bottom:
        raise ValueError("y not in bounds")

    if to_projection is coordinates.rd_projection:
        return topleft_x, topleft_y
    return coordinates.transform(
        coordinates.rd_projection, to_projection, topleft_x, topleft_y)


def bottomright_of_composite_pixel(
    x, y, to_projection=coordinates.rd_projection):
    topleft_x, topleft_y = topleft_of_composite_pixel(x, y)
    dx, dy = settings.COMPOSITE_CELLSIZE

    bottomright_x, bottomright_y = topleft_x + dx, topleft_y - dy

    if to_projection is coordinates.rd_projection:
        return bottomright_x, bottomright_y
    return coordinates.transform(
        coordinates.rd_projection, to_projection,
        bottomright_x, bottomright_y)
