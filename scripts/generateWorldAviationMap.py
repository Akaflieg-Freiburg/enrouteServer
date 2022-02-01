#!/bin/python

from datetime import date

import json
import OFMX
import openAIP2


#
# Thanks to
# https://stackoverflow.com/questions/33955225/remove-duplicate-json-objects-from-list-in-python/33955336
#
def removeduplicate(it):
    seen = set()
    for x in it:
        t = json.dumps(x)
        if t not in seen:
            yield x
            seen.add(t)


#
# Main program starts here
#

features = []
features += openAIP2.readOpenAIP()
features += OFMX.readOFMX()

# Remove duplicated entries
features = list(removeduplicate(features))

# Generate feature collection, set info string
infoString = "Generated from openAIP and open flightmaps data, {}".format(date.today())
featureCollection = {'type': 'FeatureCollection', 'info': infoString, 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('worldAviationMap.geojson', 'w')
file.write(geojson)
