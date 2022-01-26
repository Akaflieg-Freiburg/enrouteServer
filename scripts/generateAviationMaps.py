#!/bin/python

import json
import OFMX
import openAIP2

#
# Main program starts here
#

features = []

features += openAIP2.readOpenAIP()
features += OFMX.readOFMX()

# Generate Feature Collection
featureCollection = {'type': 'FeatureCollection', 'info': 'infoString', 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('test.geojson', 'w')
file.write(geojson)


