#!/usr/bin/python3

import geopandas
import json
import os

countries = [
    # Africa
    ["South Africa", "Africa/South Africa"],
    ["Madagascar", "Africa/Madagascar"],
    ["Namibia", "Africa/Namibia"],

    # Asia
    ["Japan", "Asia/Japan"],

    # Oceania Australia
    ["Australia", "Australia Oceanica/Australia"],
    ["New Zealand", "Australia Oceanica/New Zealand"],

    # Europe
    ["Austria", "Europe/Austria"],
    ["Belgium", "Europe/Belgium"],
    ["Bulgaria", "Europe/Bulgaria"],
    ["Croatia", "Europe/Croatia"],
    ["Cyprus", "Europe/Cyprus"],
    ["Czechia", "Europe/Czech Republic"],
    ["Denmark", "Europe/Denmark"],
    ["Estonia", "Europe/Estonia"],
    ["Finland", "Europe/Finland"],
    ["France", "Europe/France"],
    ["Germany", "Europe/Germany"],
    ["Greece", "Europe/Greece"],
    ["Hungary", "Europe/Hungary"],
    ["Iceland", "Europe/Iceland"],
    ["Ireland", "Europe/Ireland"],
    ["Italy", "Europe/Italy"],
    ["Latvia", "Europe/Latvia"],
    ["Liechtenstein", "Europe/Liechtenstein"],
    ["Lithuania", "Europe/Lithuania"],
    ["Luxembourg", "Europe/Luxembourg"],
    ["Malta", "Europe/Malta"],
    ["Netherlands", "Europe/Netherlands"],
    ["Norway", "Europe/Norway"],
    ["Poland", "Europe/Poland"],
    ["Portugal", "Europe/Portugal"],
    ["Romania", "Europe/Romania"],
    ["Republic of Serbia", "Europe/Serbia"],
    ["Slovakia", "Europe/Slovakia"],
    ["Slovenia", "Europe/Slowenia"],
    ["Spain", "Europe/Spain"],
    ["Sweden", "Europe/Sweden"],
    ["Switzerland", "Europe/Switzerland"],
    ["United Kingdom", "Europe/United Kingdom"],

    # North America
    ["Canada", "North America/Canada"],
    ["United States of America", "North America/United States"],

    # South America
    ["Argentina", "South America/Argentina"],
    ["Brazil", "South America/Brazil"],
    ["United Kingdom", "South America/Falkland Islands"],
]

# Extract info string from world aviation map
infoString = ''
with open('worldAviationMap.geojson') as file:
    worldAviationMapJson = json.load(file)
    infoString = worldAviationMapJson['info']
    print(infoString)
print('Splitting world aviation map {}'.format(infoString))


worldCountryMap = geopandas.read_file( 'data/ne_10m_admin_0_countries.dbf' )
os.makedirs('out/Africa', exist_ok=True)
os.makedirs('out/Asia', exist_ok=True)
os.makedirs('out/Australia Oceanica', exist_ok=True)
os.makedirs('out/Europe', exist_ok=True)
os.makedirs('out/North America', exist_ok=True)
os.makedirs('out/South America', exist_ok=True)


for country in countries:
    print('Generating map extract for ' + country[1] )
    countryGDF = worldCountryMap[worldCountryMap.SOVEREIGNT == country[0]]
    if countryGDF.size == 0:
        print('Country is empty: '+country)
        exit(-1)

    countryGDF.set_crs("EPSG:4326")
    buffer = countryGDF.buffer(0.3).set_crs("EPSG:4326")
    aviationMap = geopandas.read_file('worldAviationMap.geojson', mask=buffer)

    # Generate json
    jsonString = aviationMap.to_json(na='drop', drop_id=True)
    jsonDict = json.loads(jsonString)
    jsonDict['info'] = infoString
    jsonString = json.dumps(jsonDict, sort_keys=True, separators=(',', ':'))

    file = open('out/' + country[1] + '.geojson', 'w')
    file.write(jsonString)
