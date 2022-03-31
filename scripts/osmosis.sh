#!/bin/bash
set -e

echo "Run Osmosis"
osmosis \
    --read-pbf-fast freiburg-regbez-latest.osm.pbf \
    --tf accept-nodes place=city,town,village \
    --tf reject-ways \
    --tf reject-relations \
    \
    --read-pbf-fast freiburg-regbez-latest.osm.pbf \
    --tf accept-ways highway=motorway,trunk,primary,secondary,motorway_link,trunk_link,primary_link landuse=* railway=* water=* waterway=*\
    --tf reject-relations \
    --used-node \
    \
    --merge \
    --write-pbf out.pbf

echo "Run tilemaker"
tilemaker --verbose --input out.pbf --output ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles
rm -rf ~/.cache/QtLocation 
ls -lah *.pbf
cd ~/Software/projects/enroute/build && ninja && ./src/enroute
