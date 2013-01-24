Changelog of lizard-neerslagradar
===================================================


0.10.2 (unreleased)
-------------------

- Nothing changed yet.


0.10.1 (2013-01-24)
-------------------

- Accept shapefiles with either "NAAM" or "NAME".


0.10 (2013-01-24)
-----------------

- Superuser can see timeseries in the entire extent.

- Always have an admin interface, not just when DEBUG=True.


0.9 (2013-01-24)
----------------

- Nothing changed yet.


0.8.2 (2013-01-17)
------------------

- Remove console.log statement that gives problems in IE.


0.8.1 (2013-01-09)
------------------

- Fix bug in translating the local times back to UTC when rendering
  geotiffs.


0.8 (2013-01-08)
----------------

- Mouseovers, popups etc are now only shown if the user actually has
  access to this region (issue 8).

- Show region(s) of the logged in user as a map layer.

- Show times in the correct timezone. They are translated from UTC to
  the site's timezone settings in Python, and rendered as-is in
  Javascript.

0.7 (2013-01-03)
----------------

Adds a command 'create_reprojected_geotiffs'.

The tiffs are for the whole area, and for each user. Tiffs are created
based on the last 24 hours of production RD geotiffs. Older generated tiffs
are cleaned up by the script.

A setting GEOTIFF_ANIMATION_CACHE_DIR is needed to point to the directory
in which these tiffs should be generated.

The WmsView uses these tiffs to render Google projected image layers.


0.6 (2012-12-19)
----------------

- Uses gdalwarp / gdal_translate to make pngs for the animation
- Caches these pngs, but _doesn't delete them yet_. Don't use in
  production.
- Images for whole country and regions still don't overlap exactly.
- Added debug info to the mouseover (google, rd coordinates of
  point). Don't use in production.
- Add lizard_rainapp's herhalingstijden calculations to the popup
- CSV download works now
- Flot graphs are now bars
- Matplotlib graphs work and are bars (using RainApp graph)

0.5 (2012-12-12)
----------------

- We now use Google-projected Geotiffs and the projection is slightly
  better, but it's not the final solution yet.


0.4 (2012-12-06)
----------------

- Nothing changed yet.


0.3 (2012-12-06)
----------------

- Got a rudimentary dummy graph to work.
- Graph now shows actual timeseries data from thredds.
- Date selection functionality now works.
- Now shows data from the correct grid pixel.
- Show two animated layers when the user is logged in: whole region
  with low opacity, and the user's region with high opacity
- Region.extent_for_user() now always returns an extent that
  lines up with boundaries of the composite grid

0.2 (2012-11-29)
----------------

- Added regions; regions can be added by a script, connected to users,
  users can login and then zoom to their region, map animation will be
  confined to their region only.


0.1 (2012-11-26)
----------------

- Initial project structure created with nensskel 1.30.dev0.

- Copied the code from Erik-Jan's prototype site, and got it to work
  as a Lizard app.
