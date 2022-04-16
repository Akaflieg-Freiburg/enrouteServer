#!/usr/bin/python3

import pbf2mbtiles
import subprocess
import sys


tasks = [
    ['europe', 
        [
            ['Germany',     [5.864417, 47.26543, 15.05078, 55.14777]],
            ['Switzerland', [5.952882, 45.81617, 10.49584, 47.81126]]
        ]
    ]
]

for task in tasks:
    continent = task[0]
    maps = task[1]
    for map in maps:
        print(map[0])

print('Run Osmium tags-filter')
subprocess.run(
    ["osmium",
    "tags-filter",
    sys.argv[1],
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

pbf2mbtiles.pbf2mbtiles('out.pbf', 5.864417, 47.26543, 15.05078, 55.14777, 'Germany.mbtiles')

#subprocess.run(
#    "./pbf2mbtiles.py out.pbf 5.864417,47.26543,15.05078,55.14777 Germany.mbtiles",
#    shell=True,
#    check=True
#)

#subprocess.run(
#    "./pbf2mbtiles.py out.pbf 5.952882,45.81617,10.49584,47.81126 Switzerland.mbtiles",
#    shell=True,
#    check=True
#)

subprocess.run(
    "mv *.mbtiles /home/kebekus/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe",
    shell=True,
    check=True
)
