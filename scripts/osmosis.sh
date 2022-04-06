#!/bin/bash
set -e

echo "Run Osmium"
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

echo "Run tilemaker"
tilemaker --input out.pbf --output ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles

echo "Optimize"
./optimize.py ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles


rm -rf ~/.cache/QtLocation 
ls -lah *.pbf
ls -lah ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles
cd ~/Software/projects/enroute/build && ninja && ./src/enroute
