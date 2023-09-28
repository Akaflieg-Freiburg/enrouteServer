#!/bin/bash

rm -rf data
mkdir data

cd data
wget https://osmdata.openstreetmap.de/download/water-polygons-split-4326.zip
unzip water-polygons-split-4326.zip
rm water-polygons-split-4326.zip
cd ..


mkdir data/ne_10m_admin_0_countries
cd data/ne_10m_admin_0_countries
wget https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip
unzip ne_10m_admin_0_countries.zip
rm ne_10m_admin_0_countries.zip
cd ../..

mkdir data/ne_10m_antarctic_ice_shelves_polys
cd data/ne_10m_antarctic_ice_shelves_polys
wget https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_antarctic_ice_shelves_polys.zip
unzip ne_10m_antarctic_ice_shelves_polys.zip
rm ne_10m_antarctic_ice_shelves_polys.zip
cd ../..

mkdir data/ne_10m_glaciated_areas
cd data/ne_10m_glaciated_areas
wget https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_glaciated_areas.zip
unzip ne_10m_glaciated_areas.zip
rm ne_10m_glaciated_areas.zip
cd ../..

mkdir data/ne_10m_urban_areas
cd data/ne_10m_urban_areas
wget https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_urban_areas.zip
unzip ne_10m_urban_areas.zip
rm ne_10m_urban_areas.zip
cd ../..
