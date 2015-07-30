Changelog of lizard-neerslagradar
===================================================


1.0.3 (unreleased)
------------------

- And remove openradar imports, too.


1.0.2 (2015-07-30)
------------------

- Remove openradar & pydap dependencies


1.0.1 (2015-07-14)
------------------

- Nothing changed yet.


1.0 (2015-07-14)
----------------

- Nothing changed yet.


0.26 (2015-07-14)
-----------------

- Updated styling of popup, removed layer choice.


0.25 (2015-07-09)
-----------------

- Nothing changed yet.


0.24 (2015-07-09)
-----------------

- Added geolocation functionality.


0.23 (2015-07-08)
-----------------

- Put code with logged-in check back in place in lizard-neerslagradar.js.


0.22 (2015-07-08)
-----------------

 - Added nearcasting.
 - Removed Login. Changed WMS server for raindata to rasterstore.
 - Changed progressbar.
 - Added test to test GetGraphValues.
 - Changed deprecated imports to new imports.
 - Updated buildout to the lore of the current day.
 - Removed code related to table from popup.
 - Added 'Powered by' line to footer.
 - Removed legend.
 - Added geolocation to javascript.


0.21 (2013-08-09)
-----------------

- Get rid of progressbar when finished loading


0.20 (2013-08-09)
-----------------

- Added fews KNMI groundstation layers to default workspace
- Animation remebers state on zoom in or out (doesn't restart when stopped)


0.19 (2013-05-13)
-----------------

- Fix for error 500 when visiting the site for the first time: session key not
  available yet; we use that one for database keys.


0.18 (2013-04-12)
-----------------

- Switched off the small overview image. We want the user interface to be
  smaller.

- Moved play/pause button, progress bar etc to the bar above the map, so no
  longer in its own floating window. Nice!

- After loading the tiles, the animation starts automatically.

- Only the time is shown next to the progress bar, no longer the
  date. Cleaner, and it is clear anyway that it's today/yesterday. Also the
  start/stop button doesn't have text anymore; the icon is clear enough on its
  own.

- The page http-refreshes every 5 (and a bit) minutes.

- No more 'add-to-collage' link.


0.17 (2013-04-08)
-----------------

- Added initialization of request's session in the right place.


0.16 (2013-04-08)
-----------------

- Fixed date-shifting timezone-related problem.


0.15 (2013-04-04)
-----------------

- Removed some more clutter from the animation window.


0.14 (2013-04-04)
-----------------

- Less cluttered user interface (based on ideas by Wytze):

  - Sidebar gone.

  - Floating window with the progress indicator and 'run' button.

  - When the loading is done, the progress indicator disappears and the 'run'
    button is shown.

  - Sidebar buttons at the bottom are gone, too.

- Progress bar loses its I'm-busy-loading-stripes when finished.

- Using username for popup name. This selects exactly the right
  name. Otherwise we'd pick one of the regions the click was made in, which
  wouldn't always select the right one.


0.13 (2013-03-27)
-----------------

- Comfortable admin for the regions (attached users are now shown and you can
  search regions by name).

- Disabled the purple layer over the selected region.


0.12 (2013-03-27)
-----------------

- Modified location name (mostly in the graph). No longer the debug-like
  "Nieuwegein, cel (123, 456)", but the less-informative but nicer-looking
  "Neerslag in Nieuwegein".

- Hiding the date selector for not-logged-in users.

- Not logged in users get a 'contact us' popup when searching. Override the
  ``lizard_neerslagradar/contact_us.html`` template in the site with what you
  really want in the popup.


0.11 (2013-03-21)
-----------------

- Anonymous users get 3 hours of animation, logged-in ones get 24.

- Added legend.

- Require at least openradar 0.3.1


0.10.2 (2013-02-14)
-------------------

- Use openradar package to get values from opendap for graph.


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
