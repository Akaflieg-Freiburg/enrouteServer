#!/bin/bash
set -e

cp Germany.mbtiles ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/
./optimize.py ~/.local/share/Akaflieg\ Freiburg/enroute\ flight\ navigation/aviation_maps/Europe/Germany.mbtiles

rm -rf ~/.cache/QtLocation -rvf
cd ~/Software/projects/enroute/build && ninja && ./src/enroute