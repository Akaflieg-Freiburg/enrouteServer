#!/usr/bin/python3

import os
import subprocess
import sys
import vector_tile


tasks = [
    ['North America',
     'https://download.geofabrik.de/north-america-latest.osm.pbf',
     [
         ['Canada', [-141.7761,41.6377, -44.17684, 85.04032]],
         ['USA Midwest', [-104.0588, 35.98507, -80.50521, 49.40714]],
         ['USA Northeast', [-80.52632, 38.77178, -66.87576, 47.48423]],
         ['USA Pacific', [-179.9965, 15.98281, -129.7998, 72.98845]],
         ['USA South', [-106.6494, 24.20031, -71.50981, 40.64636]],
         ['USA West', [-133.0637, 31.32659, -102.041, 49.45605]]
     ]],
    ['South America',
     'https://download.geofabrik.de/south-america-latest.osm.pbf',
     [
         ['Argentina', [-73.61453, -55.68296, -53.59024, -21.72575]],
         ['Brazil', [-74.09056, -35.46552, -27.67249, 5.522895]]
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
    subprocess.run(['curl', task[1], "--output", "download.pbf"], check=True)

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
    os.remove('out.pbf')
    break

exit(-1)

vector_tile.pbf2mbtiles('out.pbf', 5.952882, 45.81617, 10.49584, 47.81126, 'Switzerland')

subprocess.run(
    "mv *.mbtiles /home/kebekus/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe",
    shell=True,
    check=True
)
