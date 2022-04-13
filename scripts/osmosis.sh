#!/bin/bash
set -e

echo "Run Osmium tags-filter"
osmium tags-filter \
    $1 \
    /aerialway=cable_car,gondola,zip_line,goods \
    /aeroway \
    /admin_level=2 \
    /highway=motorway,trunk,primary,secondary,motorway_link \
    /landuse \
    /natural \
    /place=city,town,village \
    /railway \
    /water \
    /waterway \
    -o out.pbf \
    --overwrite

./pbf2mbtiles.py out.pbf 5.864417,47.26543,15.05078,55.14777 Germany.mbtiles
#./pbf2mbtiles.py out.pbf 5.952882,45.81617,10.49584,47.81126 Switzerland.mbtiles

mv *.mbtiles /home/kebekus/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe
~/Software/projects/enroute/build/src/enroute
