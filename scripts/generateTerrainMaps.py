#!/usr/bin/python3

import math
import os
import requests
import sqlite3
import subprocess

from datetime import date

tasks = [
    ['Africa',
     'https://download.geofabrik.de/africa-latest.osm.pbf',
     [
      ['Canary Islands', [-18.92352, 26.36117, -12.47875, 30.25648]],
      ['Namibia', [9.784615, -30.07236, 25.29929, -16.91682]],
      ['South Africa', [15.99606, -47.58493, 39.24259, -22.11736]]
     ]],
    ['Asia',
     'https://download.geofabrik.de/asia/japan-latest.osm.pbf',
     [
      ['Japan', [122.5607, 21.20992, 153.8901, 45.80245]]
     ]],
    ['Australia Oceanica',
     'https://download.geofabrik.de/australia-oceania-latest.osm.pbf',
     [
      ['Australia', [109.9694, -45.95665, 169.0016, -8.937109]],
      ['New Zealand', [162.096, -48.77, 179.8167, -32.667]]
     ]],
    ['Europe',
     'https://download.geofabrik.de/europe-latest.osm.pbf',
     [
      ['Austria', [9.52678, 46.36851, 17.16273, 49.02403]],
      ['Belgium', [2.340725, 49.49196, 6.411619, 51.59839]],
      ['Bulgaria', [22.34875, 41.22681, 29.18819, 44.22477]],
      ['Croatia', [13.08916, 42.16483, 19.45911, 46.56498]],
      ['Cyprus', [31.95244, 34.23374, 34.96147, 36.00323]],
      ['Czech Republic', [12.08477, 48.54292, 18.86321, 51.06426]],
      ['Denmark', [7.7011, 54.44065, 15.65449, 58.06239]],
      ['Estonia', [20.85166, 57.49764, 28.21426, 59.99705]],
      ['Finland', [19.02427, 59.28783, 31.60089, 70.09959]],
      ['France', [-6.3, 41.27688, 9.8, 51.32937]],
      ['Germany', [5.864417, 47.26543, 15.05078, 55.14777]],
      ['Great Britain', [-9.408655, 49.00443, 2.25, 61.13564]],
      ['Greece', [19.15881, 34.59111, 29.65683, 41.74954]],
      ['Hungary', [16.11262, 45.73218, 22.90201, 48.58766]],
      ['Iceland', [-25.7, 62.84553, -12.41708, 67.50085]],
      ['Ireland and Northern Ireland', [-12.57937, 49.60002, -5.059265, 56.64261]],
      ['Italy', [6.602696, 35.07638, 19.12499, 47.10169]],
      ['Latvia', [20.79407, 55.66886, 28.24116, 58.08231]],
      ['Liechtenstein', [9.471078, 47.04774, 9.636217, 47.27128]],
      ['Lithuania', [20.63822, 53.89605, 26.83873, 56.45106]],
      ['Luxembourg', [5.733033, 49.44553, 6.532249, 50.18496]],
      ['Malta', [14.0988, 35.77776, 14.61755, 36.11909]],
      ['Netherlands', [2.992192, 50.74753, 7.230455, 54.01786]],
      ['Norway', [-11.36801, 57.55323, 35.52711, 81.05195]],
      ['Poland', [14.0998, 48.98568, 24.16522, 55.09949]],
      ['Portugal', [-31.5, 32.0, -6.179513, 42.1639]],
      ['Romania', [20.24181, 43.59703, 30.27896, 48.28633]],
      ['Serbia', [18.82347, 42.24909, 23.00617, 46.19125]],
      ['Slovakia', [16.8284, 47.72646, 22.57051, 49.6186]],
      ['Slovenia', [13.36653, 45.41273, 16.61889, 46.88667]],
      ['Spain', [-9.779014, 35.73509, 5.098525, 44.14855]],
      ['Sweden', [10.54138, 55.02652, 24.22472, 69.06643]],
      ['Switzerland', [5.952882, 45.81617, 10.49584, 47.81126]]
     ]],
    ['North America',
     'https://download.geofabrik.de/north-america-latest.osm.pbf',
     [
         ['Canada', [-141.7761,41.6377, -44.17684, 85.04032]],
         ['USA Midwest', [-104.0588, 35.98507, -80.50521, 49.40714]],
         ['USA Northeast', [-80.52632, 38.77178, -66.87576, 47.48423]],
         ['USA Pacific', [-179.9965, 15.98281, -129.7998, 72.98845]],
         ['USA South', [-106.6494, 24.20031, -71.50981, 40.64636]],
         ['USA West', [-133.0637, 31.32659, -102.041, 49.45605]]
     ]],
    ['South America',
     'https://download.geofabrik.de/south-america-latest.osm.pbf',
     [
         ['Argentina', [-73.61453, -55.68296, -53.59024, -21.72575]],
         ['Brazil', [-74.09056, -35.46552, -27.67249, 5.522895]]
     ]]
]

def deg2num(lat_deg, lon_deg, zoom):
    """
    Converts coordinate to tile number
    taken from
    https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon..2Flat._to_tile_numbers_2
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def png2webp(blob):
    with open('x-in.png','wb') as f:
       f.write(blob)
       f.close()

    subprocess.run(
        ["cwebp",
        "x-in.png",
        "-z", "9",
        "-quiet",
        "-noalpha",
        "-o", "x-out.webp"],
        check=True
    )
    newBlob = open('x-out.webp', 'rb').read()
    os.remove('x-in.png')
    os.remove('x-out.webp')
    return newBlob


zoomMin = 7
zoomMax = 10

attribution = """ArcticDEM terrain data DEM(s) were created from DigitalGlobe, Inc., imagery and funded under National Science Foundation awards 1043681, 1559691, and 1542736. 
Australia terrain data © Commonwealth of Australia (Geoscience Australia) 2017. 
Austria terrain data © offene Daten Österreichs – Digitales Geländemodell (DGM) Österreich. 
Canada terrain data contains information licensed under the Open Government Licence – Canada. 
Europe terrain data produced using Copernicus data and information funded by the European Union - EU-DEM layers. 
Global ETOPO1 terrain data U.S. National Oceanic and Atmospheric Administration. 
Mexico terrain data source: INEGI, Continental relief, 2016. 
New Zealand terrain data Copyright 2011 Crown copyright (c) Land Information New Zealand and the New Zealand Government (All rights reserved). 
Norway terrain data © Kartverket. 
United Kingdom terrain data © Environment Agency copyright and/or database right 2015. All rights reserved. 
United States 3DEP (formerly NED) and global GMTED2010 and SRTM terrain data courtesy of the U.S. Geological Survey. 
""".replace('\n', '<br>')

for task in tasks:
    continent = task[0]
    maps = task[2]

    for map in maps:
        country = map[0]

        fileName = 'out/'+continent+'/'+country+'.terrain'
        if os.path.exists(fileName):
            print("Terrain data for {} already exists. Skipping.".format(country))
            continue
        print("Working on country {}.".format(country))

        dbConnection = None
        try:
            os.remove('tmp.terrain')
        except BaseException as err:
            True
        dbConnection = sqlite3.connect('tmp.terrain')
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE metadata (name text, value text)')
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('name', '{}')".format(continent+'/'+country))
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('type', 'baselayer')")
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('version', '{}')".format(date.today().strftime("%d-%b-%Y")))
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('description', 'Terrain data for Enroute Flight Navigation')")
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('format', 'webp')")
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('encoding', 'terrarium')")
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('maxzoom', ?)", (str(zoomMax),))
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('minzoom', ?)", (str(zoomMin),))
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('attribution', ?)", (attribution,))
        bboxString = str(map[1][0])+','+str(map[1][1])+','+str(map[1][2])+','+str(map[1][3])
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('bounds', '{}')".format(bboxString))
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('attribution', 'None yet')")

        cursor.execute('CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)')
        for zoom in range(zoomMin, zoomMax+1):
            (xmin, ymax) = deg2num(map[1][1], map[1][0], zoom)
            (xmax, ymin) = deg2num(map[1][3], map[1][2], zoom)
            for x in range(xmin, xmax+1):
                for y in range(ymin, ymax+1):
                    try:
                        response = requests.get(' https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{}/{}/{}.png'.format(zoom, x, y))
                        response.raise_for_status()
                        # Code here will only run if the request is successful
                    except requests.exceptions.HTTPError as errh:
                        print(errh)
                        exit(-1)
                    except requests.exceptions.ConnectionError as errc:
                        print(errc)
                        exit(-1)
                    except requests.exceptions.Timeout as errt:
                        print(errt)
                        exit(-1)
                    except requests.exceptions.RequestException as err:
                        print(err)
                        exit(-1)
                    yflipped = 2**zoom-1-y
                    blob = png2webp(response.content)
                    cursor.execute("INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)", (zoom, x, yflipped, blob))
                    print(zoom, x, y)
       
        dbConnection.commit()

        cursor.execute("CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row)")
        dbConnection.commit()

        cursor.execute("vacuum")
        dbConnection.commit()

        cursor.close()
        dbConnection.commit()
        dbConnection.close()

        os.makedirs("out/"+continent, exist_ok=True)
        os.rename('tmp.terrain', fileName)

        exit(-1)

    break
