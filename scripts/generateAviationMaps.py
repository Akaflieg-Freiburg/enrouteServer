#!/bin/python

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
#WRONG!!!!!
        t = json.dumps(it)
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

# Generate Feature Collection
featureCollection = {'type': 'FeatureCollection', 'info': 'infoString', 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('world.geojson', 'w')
file.write(geojson)


