# fetch-global-weather-data

readWatherData.py fetches most recent global wind data directly to array using nomads API format. Data is then plotted used matlab quiver plot.

haversine.py determines distance between two lat + long points.

requirements:
netCDF4
numpy
matplotlib

Can be adjusted for higher accuracy data (1p00 => 0p25).
Date may also be adjusted to some extent (NOT TESTED YET)
