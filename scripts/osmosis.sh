#!/bin/bash
set -e

echo "Run Osmosis"
echo \
    --read-pbf-fast $1 \
    --tf accept-nodes place=city,town,village \
    --tf reject-ways \
    --tf reject-relations \
    \
    --read-pbf-fast $1 \
    --tf accept-ways boundary=* highway=motorway,trunk,primary,secondary,motorway_link,trunk_link landcover=* landuse=* leisure=* natural=* railway=* water=* waterway=*\
    --used-node \
    \
    --merge \
    --write-pbf out.pbf


osmium tags-filter \
    $1 \
    /aerialway=cable_car,gondola,zip_line,goods \
    w/admin_level=2 \
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
#tilemaker --input $1 --output ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles

echo "Optimize"
#./optimize.py ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles


rm -rf ~/.cache/QtLocation 
ls -lah *.pbf
ls -lah ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles
cd ~/Software/projects/enroute/build && ninja && ./src/enroute
