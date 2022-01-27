#!/bin/python3

import geopandas

gdf_mask = geopandas.read_file( geopandas.datasets.get_path("naturalearth_lowres") )
germany = gdf_mask[gdf_mask.name=="Germany"]
print(germany)

world = geopandas.read_file('world.geojson', mask=germany)
jsonString = world.to_json(na='drop')
file = open('Germany.geojson', 'w')
file.write(jsonString)
