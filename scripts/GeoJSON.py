#!/bin/python3

from itertools import count
import geopandas

gdf_mask = geopandas.read_file( geopandas.datasets.get_path("naturalearth_lowres") )

countries = [
    ["Africa", "South Africa"],
    ["Africa", "Namibia"],
    ["Asia", "Japan"],
    ["Australia Oceanica", "Australia"],
    ["Australia Oceanica", "New Zealand"],
    ["Europe", "Austria"],
    ["Europe", "Belgium"],
    ["Europe", "Bulgaria"],
    ["Europe", "Croatia"],
    ["Europe", "Cyprus"],
    ["Europe", "Czech Republic"],
    ["Europe", "Denmark"],
    ["Europe", "Estonia"],
    ["Europe", "Finland"],
    ["Europe", "France"],
    ["Europe", "Germany"],
    ["Europe", "Greece"],
    ["Europe", "Hungary"],
    ["Europe", "Iceland"],
    ["Europe", "Ireland"],
    ["Europe", "Italy"],
    ["Europe", "Latvia"],
    ["Europe", "Liechtenstein"],
    ["Europe", "Lithuania"],
    ["Europe", "Luxembourg"],
    ["Europe", "Malta"],
    ["Europe", "Netherlands"],
    ["Europe", "Norway"],
    ["Europe", "Poland"],
    ["Europe", "Portugal"],
    ["Europe", "Romania"],
    ["Europe", "Serbia"],
    ["Europe", "Slovakia"],
    ["Europe", "Slowenia"],
    ["Europe", "Spain"],
    ["Europe", "Sweden"],
    ["Europe", "Switzerland"],
    ["Europe", "United Kingdom"],
    ["North America", "Canada"],
    ["North America", "United States"],
    ["South America", "Argentina"],
    ["South America", "Brazil"],
    ["South America", "Falkland Islands", "fk"],
]

for country in countries:
    print('Generating map extract for ' + country[1] )
    countryGDF = gdf_mask[gdf_mask.name == country[1]]
    if countryGDF.size == 0:
        print('Country is empty: '+country)
        exit(-1)

    world = geopandas.read_file('world.geojson', mask=countryGDF)
    jsonString = world.to_json(na='drop')
    file = open(country[0] + "_" + country[1] + '.geojson', 'w')
    file.write(jsonString)
