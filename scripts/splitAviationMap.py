#!/bin/python3

import geopandas
import json


countries = [
    # Africa
    ["South Africa", "Africa_South Africa"],
    ["Namibia", "Africa_Namibia"],

    # Asia
    ["Japan", "Asia_Japan"],

    # Oceania Australia
    ["Australia", "Australia Oceanica_Australia"],
    ["New Zealand", "Australia Oceanica_New Zealand"],

    # Europe
    ["Austria", "Europe_Austria"],
    ["Belgium", "Europe_Belgium"],
    ["Bulgaria", "Europe_Bulgaria"],
    ["Croatia", "Europe_Croatia"],
    ["Cyprus", "Europe_Cyprus"],
    ["Czechia", "Europe_Czech Republic"],
    ["Denmark", "Europe_Denmark"],
    ["Estonia", "Europe_Estonia"],
    ["Finland", "Europe_Finland"],
    ["France", "Europe_France"],
    ["Germany", "Europe_Germany"],
    ["Greece", "Europe_Greece"],
    ["Hungary", "Europe_Hungary"],
    ["Iceland", "Europe_Iceland"],
    ["Ireland", "Europe_Ireland"],
    ["Italy", "Europe_Italy"],
    ["Latvia", "Europe_Latvia"],
    ["Liechtenstein", "Europe_Liechtenstein"],
    ["Lithuania", "Europe_Lithuania"],
    ["Luxembourg", "Europe_Luxembourg"],
    ["Malta", "Europe_Malta"],
    ["Netherlands", "Europe_Netherlands"],
    ["Norway", "Europe_Norway"],
    ["Poland", "Europe_Poland"],
    ["Portugal", "Europe_Portugal"],
    ["Romania", "Europe_Romania"],
    ["Republic of Serbia", "Europe_Serbia"],
    ["Slovakia", "Europe_Slovakia"],
    ["Slovenia", "Europe_Slowenia"],
    ["Spain", "Europe_Spain"],
    ["Sweden", "Europe_Sweden"],
    ["Switzerland", "Europe_Switzerland"],
    ["United Kingdom", "Europe_United Kingdom"],

    # North America
    ["Canada", "North America_Canada"],
    ["United States of America", "North America_United States"],

    # South America
    ["Argentina", "South America_Argentina"],
    ["Brazil", "South America_Brazil"],
    ["United Kingdom", "South America_Falkland Islands"],
]

# Extract info string from world aviation map
infoString = ''
with open('worldAviationMap.geojson') as file:
    worldAviationMapJson = json.load(file)
    infoString = worldAviationMapJson['info']
    print(infoString)
print('Splitting world aviation map {}'.format(infoString))


worldCountryMap = geopandas.read_file( 'data/ne_10m_admin_0_countries.dbf' )

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
    jsonString = aviationMap.to_json(na='drop')
    jsonDict = json.loads(jsonString)
    jsonDict['info'] = infoString
    jsonString = json.dumps(jsonDict, sort_keys=True, separators=(',', ':'))

    file = open(country[1] + '.geojson', 'w')
    file.write(jsonString)
