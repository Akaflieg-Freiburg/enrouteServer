#!/bin/bash

cd /mnt/storage/mbtiles

echo "Clear working directory…"
rm -rv working
mkdir -p working/Africa
mkdir -p working/Australia\ Oceania
mkdir -p working/Europe
mkdir -p working/North\ America


echo "Copy files into working directory"

# Africa
cp -v raw/osm-2017-07-03-v3.6.1-africa_namibia.mbtiles working/Africa/Namibia.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-africa_south-africa.mbtiles working/Africa/South\ Africa.mbtiles

# Australia Oceania
cp -v raw/osm-2017-07-03-v3.6.1-australia-oceania_australia.mbtiles working/Australia\ Oceania/Australia.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-australia-oceania_new-zealand.mbtiles working/Australia\ Oceania/New\ Zealand.mbtiles

# Europe - EU27
cp -v raw/osm-2017-07-03-v3.6.1-europe_austria.mbtiles working/Europe/Austria.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_belgium.mbtiles working/Europe/Belgium.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_bulgaria.mbtiles working/Europe/Bulgaria.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_croatia.mbtiles working/Europe/Croatia.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_cyprus.mbtiles working/Europe/Cyprus.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_czech-republic.mbtiles working/Europe/Czech\ Republic.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_denmark.mbtiles working/Europe/Denmark.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_estonia.mbtiles working/Europe/Estonia.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_finland.mbtiles working/Europe/Finland.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_france.mbtiles working/Europe/France.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_germany.mbtiles working/Europe/Germany.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_greece.mbtiles working/Europe/Greece.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_hungary.mbtiles working/Europe/Hungary.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_ireland-and-northern-ireland.mbtiles working/Europe/Ireland\ and\ Northern\ Ireland.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_italy.mbtiles working/Europe/Italy.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_latvia.mbtiles working/Europe/Latvia.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_lithuania.mbtiles working/Europe/Lithuania.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_luxembourg.mbtiles working/Europe/Luxembourg.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_malta.mbtiles working/Europe/Malta.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_netherlands.mbtiles working/Europe/Netherlands.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_poland.mbtiles working/Europe/Poland.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_portugal.mbtiles working/Europe/Portugal.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_romania.mbtiles working/Europe/Romania.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_slovakia.mbtiles working/Europe/Slovakia.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_slovenia.mbtiles working/Europe/Slovenia.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_spain.mbtiles working/Europe/Spain.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_sweden.mbtiles working/Europe/Sweden.mbtiles

# Europe - other
cp -v raw/osm-2017-07-03-v3.6.1-europe_great-britain.mbtiles working/Europe/Great\ Britain.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_iceland.mbtiles working/Europe/Iceland.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_liechtenstein.mbtiles working/Europe/Liechtenstein.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_norway.mbtiles working/Europe/Norway.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-europe_switzerland.mbtiles working/Europe/Switzerland.mbtiles

# North America
cp -v raw/osm-2017-07-03-v3.6.1-north-america_canada.mbtiles working/North\ America/Canada.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-north-america_us-midwest.mbtiles working/North\ America/USA\ Midwest.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-north-america_us-northeast.mbtiles working/North\ America/USA\ Northeast.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-north-america_us-pacific.mbtiles working/North\ America/USA\ Pacific.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-north-america_us-south.mbtiles working/North\ America/USA\ South.mbtiles
cp -v raw/osm-2017-07-03-v3.6.1-north-america_us-west.mbtiles working/North\ America/USA\ West.mbtiles


# Shrink tiles
find working -name "*.mbtiles" | parallel -v /home/kebekus/Software/projects/enroute/serverScripts/shrinkTiles.py '{}'

# Move tiles to new place
echo "Move tiles to Austausch/aviation_maps/OpenMapTiles"
rm -rf /home/kebekus/Austausch/aviation_maps/OpenMapTiles/*
mv working/* /home/kebekus/Austausch/aviation_maps/OpenMapTiles

# Delete working directory
rm -rf working
