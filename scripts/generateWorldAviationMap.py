from datetime import date

import geopy.distance
import json
import math
import OFMX
import openAIP2


#
# This generator function does two things. First, it removes all duplicate items
# from the list. Second, it searches for reporting points that are less than
# 1000m apart.  These duplicate reporting points may enter the list because we
# import reporting points from openAIP and from open flightmaps.
#
# Thanks to
# https://stackoverflow.com/questions/33955225/remove-duplicate-json-objects-from-list-in-python/33955336
#
def removeduplicate(it):
    # This is a set of feature that we have already seen
    seen = set()

    # Coordinates of reporting points that we have already seen, bucketed into
    # latitude bands of 0.01°. One band spans at least 1.105km on the WGS84
    # ellipsoid, so two points less than 1km apart always lie in the same or in
    # adjacent bands. This way, each new point needs to be compared only
    # against the points in three bands, not against all points seen so far.
    reportingPointBands = {}
    for x in it:

        # If the item has been seen, then skip it
        t = json.dumps(x)
        if t in seen:
            continue

        # If the item is a waypoint whose coordinates are already in the list
        # (up to 1000m tolerance), then also skip it
        if x['properties']['TYP'] == 'WP':
            coord = x['geometry']['coordinates']
            band = math.floor(coord[1] / 0.01)

            # Upper bound (with >20% safety margin) for the longitude
            # difference of two points less than 1km apart. Points whose
            # longitudes differ by more cannot be within 1km, so the expensive
            # geodesic computation is skipped for them.
            cosLat = math.cos(math.radians(min(abs(coord[1]) + 0.01, 90.0)))
            maxLonDiff = 0.011 / max(cosLat, 1e-9)

            hasRP = False
            for b in (band - 1, band, band + 1):
                for exCoord in reportingPointBands.get(b, []):
                    lonDiff = abs(coord[0] - exCoord[0])
                    if lonDiff > 180.0:  # wrap around at the antimeridian
                        lonDiff = 360.0 - lonDiff
                    if lonDiff > maxLonDiff:
                        continue
                    # geopy expects point coordinates in an order that differs from GeoJSON conventions
                    A = [coord[1], coord[0]]
                    B = [exCoord[1], exCoord[0]]
                    if geopy.distance.geodesic(A, B).km < 1.0:
                        hasRP = True
                        break
                if hasRP:
                    break
            if hasRP:
                continue
            reportingPointBands.setdefault(band, []).append(coord)

        # Yield the element, and add it to the list of elements that we have
        # already seen.
        yield x
        seen.add(t)


#
# Main program starts here
#

features = []
features += OFMX.readOFMX() # OFMX comes first, because we trust OFMX most
features += openAIP2.readOpenAIP()

# Remove duplicated entries
features = list(removeduplicate(features))

# Generate feature collection, set info string
infoString = "Generated from openAIP and open flightmaps data, {}".format(date.today())
featureCollection = {'type': 'FeatureCollection', 'info': infoString, 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('worldAviationMap.geojson', 'w')
file.write(geojson)
