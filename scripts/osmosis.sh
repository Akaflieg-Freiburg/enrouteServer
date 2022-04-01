#!/bin/bash
set -e

echo "Run Osmosis"
osmosis \
    --read-pbf-fast $1 \
    --tf accept-nodes place=city,town,village \
    --tf reject-ways \
    --tf reject-relations \
    \
    --read-pbf-fast $1 \
    --tf accept-ways highway=motorway,trunk,primary,secondary,motorway_link,trunk_link landcover=* landuse=* railway=* water=* waterway=*\
    --tf reject-relations \
    --used-node \
    \
    --merge \
    --write-pbf out.pbf

echo "Run tilemaker"
tilemaker --input out.pbf --output ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles

echo "Optimize"
./optimize.py ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles


rm -rf ~/.cache/QtLocation 
ls -lah *.pbf
ls -lah ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles
cd ~/Software/projects/enroute/build && ninja && ./src/enroute
