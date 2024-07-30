#!/usr/bin/python3

from datetime import date

import json
import openAIP2


#
# Main program starts here
#

features = []
# features += openAIP2.readOpenAIP()
features += openAIP2.readOpenAIPAirspaces()

# Generate feature collection, set info string
infoString = "Generated from openAIP and open flightmaps data, {}".format(date.today())
featureCollection = {'type': 'FeatureCollection', 'info': infoString, 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('testAviationMap.geojson', 'w')
file.write(geojson)
