#!/usr/bin/python3

from datetime import date

import geopy.distance
import json
import OFMX
import openAIP2


#
# This generator function does two things. First, it removes all duplicate items
# from the list. Second, it searches for reporting points that are less than
# 100m apart.  These duplicate reporting points may enter the list because we
# import reporting points from openAIP and from open flightmaps.
#
# The current implementation is seriously slow and should be improved.
#
# Thanks to
# https://stackoverflow.com/questions/33955225/remove-duplicate-json-objects-from-list-in-python/33955336
#
def removeduplicate(it):
    # This is a set of feature that we have already seen
    seen = set()

    # This is a list of reporting point coordinates that we have already seen.
    reportingPointCoordinates = []
    for x in it:

        # If the item has been seen, then skip it
        t = json.dumps(x)
        if t in seen:
            continue

        # If the item is a waypoint whose coordinates are already in the list
        # (up to 100m tolerance), then also skip it
        if x['properties']['TYP'] == 'WP':
            coord = x['geometry']['coordinates']
            hasRP = False
            for exCoord in reportingPointCoordinates:
                if geopy.distance.geodesic(coord, exCoord).km < 0.1:
                    hasRP = True
                    break
            if hasRP:
                print(x)
                continue
            reportingPointCoordinates.append(coord)
        
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
