#!/usr/bin/python3

import os
import subprocess
import sys
import vector_tile


tasks = [
    ['South America',
     'https://download.geofabrik.de/south-america-latest.osm.pbf',
     [
         ['Argentina',     [-73.61453,  -55.68296, -53.59024, -21.72575]],
         ['Brazil',        [-74.09056,  -35.46552, -27.67249,   5.522895]]
     ]]
#    ['europe',
#        [
#            ['Germany',       [5.864417, 47.26543, 15.05078, 55.14777]],
#            ['Switzerland',   [5.952882, 45.81617, 10.49584, 47.81126]]
#        ]]
]

for task in tasks:
    continent = task[0]
    maps = task[2]
    print('Download {}'.format(continent))
#    os.remove('download.pbf')
    subprocess.run( ['curl', task[1], "--output", "download.pbf"], check=True )

    print('Run Osmium tags-filter')
    subprocess.run(
        ["osmium",
        "tags-filter",
        'download.pbf',
        "/aerialway=cable_car,gondola,zip_line,goods",
        "/aeroway",
        "/admin_level=2",
        "/highway=motorway,trunk,primary,secondary,motorway_link",
        "/landuse",
        "/natural",
        "/place=city,town,village",
        "/railway",
        "/water",
        "/waterway",
        "-o", "out.pbf",
        "--overwrite"],
        check=True
    )
    os.remove('download.pbf')
    
    for map in maps:
        country = map[0]
        bbox = map[1]

        vector_tile.pbf2mbtiles('out.pbf', bbox[0], bbox[1], bbox[2], bbox[3], country)
    break
    os.remove('out.pbf')

exit(-1)

vector_tile.pbf2mbtiles('out.pbf', 5.952882, 45.81617, 10.49584, 47.81126, 'Switzerland')

subprocess.run(
    "mv *.mbtiles /home/kebekus/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe",
    shell=True,
    check=True
)
