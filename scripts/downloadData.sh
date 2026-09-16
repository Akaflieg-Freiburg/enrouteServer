#!/bin/bash
#
# Downloads the external data sets that base map generation needs into 'data/':
# OSM water polygons and several Natural Earth shapefiles. Run this script from
# inside 'scripts/'.
#
# Everything is downloaded into 'data.new' first. An existing 'data/' directory
# is only replaced once every download and extraction has succeeded, so a
# failed download never destroys a working data set. Any error aborts the
# script.

set -euo pipefail

rm -rf data.new
mkdir data.new

cd data.new
wget https://osmdata.openstreetmap.de/download/water-polygons-split-4326.zip
unzip water-polygons-split-4326.zip
rm water-polygons-split-4326.zip
cd ..


mkdir data.new/ne_10m_admin_0_countries
cd data.new/ne_10m_admin_0_countries
wget https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip
unzip ne_10m_admin_0_countries.zip
rm ne_10m_admin_0_countries.zip
cd ../..

mkdir data.new/ne_10m_antarctic_ice_shelves_polys
cd data.new/ne_10m_antarctic_ice_shelves_polys
wget https://naciscdn.org/naturalearth/10m/physical/ne_10m_antarctic_ice_shelves_polys.zip
unzip ne_10m_antarctic_ice_shelves_polys.zip
rm ne_10m_antarctic_ice_shelves_polys.zip
cd ../..

mkdir data.new/ne_10m_glaciated_areas
cd data.new/ne_10m_glaciated_areas
wget https://naciscdn.org/naturalearth/10m/physical/ne_10m_glaciated_areas.zip
unzip ne_10m_glaciated_areas.zip
rm ne_10m_glaciated_areas.zip
cd ../..

mkdir data.new/ne_10m_urban_areas
cd data.new/ne_10m_urban_areas
wget https://naciscdn.org/naturalearth/10m/cultural/ne_10m_urban_areas.zip
unzip ne_10m_urban_areas.zip
rm ne_10m_urban_areas.zip
cd ../..

# Every download succeeded: replace the old data directory with the new one.
rm -rf data
mv data.new data

# Verify that every data source listed in the tilemaker configuration is usable.
python3 -c 'import vector_tile; vector_tile.checkTilemakerSources(vector_tile.tilemakerConfigFileName)'
echo "All tilemaker data sources are in place."
