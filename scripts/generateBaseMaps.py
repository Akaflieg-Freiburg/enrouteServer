#!/usr/bin/python3

import os
import subprocess
import vector_tile

import regions

for continent in regions.continents:
    print('Download {}'.format(continent['name']))
    try:
        os.remove('download.pbf')
    except BaseException as err:
        True
    subprocess.run(['curl', continent['osmUrl'], "-L",
                   "--output", "download.pbf"], check=True)

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

    for region in [region for region in regions.regions if (region['continent'] == continent['name'])]:
        bbox = region['bbox']
        vector_tile.pbf2mbtiles(
            'out.pbf', bbox[0], bbox[1], bbox[2], bbox[3], region['name'])
        try:
            os.remove("out/"+continent['name']+"/"+region['name']+'.mbtiles')
        except BaseException as err:
            True
        os.makedirs("out/"+continent['name'], exist_ok=True)
        os.replace(region['name']+'.mbtiles', "out/"+continent['name']+"/"+region['name']+'.mbtiles')
    os.remove('out.pbf')
