#!/usr/bin/python3

import geopandas
import json
import os
import sys

import regions

# Extract info string from world aviation map
infoString = ''
with open('worldAviationMap.geojson') as file:
    worldAviationMapJson = json.load(file)
    infoString = worldAviationMapJson['info']
    print(infoString)
print('Splitting world aviation map {}'.format(infoString))


worldCountryMap = geopandas.read_file( 'data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.dbf' )

myRegion = ""
if len(sys.argv) > 1:
    myRegion = sys.argv[1]
myRegions = [region for region in regions.regions if myRegion in region['name'] or myRegion in region['continent']]

currentContinent = ''

for region in myRegions:
    if currentContinent != region['continent']:
        currentContinent = region['continent']
        print('')
        print(currentContinent)

    print('Generating map extract for ' + region["name"] )

    buffer = regions.bufferedBoundary(region)
    aviationMap = geopandas.read_file('worldAviationMap.geojson', mask=buffer)

    # Generate json
    jsonString = aviationMap.to_json(na='drop', drop_id=True)
    jsonDict = json.loads(jsonString)
    jsonDict['info'] = infoString
    jsonString = json.dumps(jsonDict, sort_keys=True, separators=(',', ':'))

    os.makedirs('out/' + region["continent"], exist_ok=True)
    file = open('out/' + region["continent"] + '/' + region["name"] + '.geojson', 'w')
    file.write(jsonString)
