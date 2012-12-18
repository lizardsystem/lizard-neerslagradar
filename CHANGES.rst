Changelog of lizard-neerslagradar
===================================================


0.6 (unreleased)
----------------

- Uses gdalwarp / gdal_translate to make pngs for the animation
- Caches these pngs, but _doesn't delete them yet_. Don't use in
  production.
- Images for whole country and regions still don't overlap exactly.
- Added debug info to the mouseover (google, rd coordinates of
  point). Don't use in production.
- Add lizard_rainapp's herhalingstijden calculations to the popup
- CSV download works now


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
