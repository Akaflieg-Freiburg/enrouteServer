#!/usr/bin/python3

import math
import multiprocessing
import os
from urllib import response
import pyprind
import requests
import sqlite3
import subprocess
import time

from datetime import date

import regions


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


def getWebp(zoom, x, y):

    retries = 1
    success = False
    while not success:
        try:
            response = requests.get(
                'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{}/{}/{}.png'.format(zoom, x, y))
            response.raise_for_status()
            success = True
        except Exception as e:
            wait = retries * 30
            print('Error! Waiting %s secs and re-trying...' % wait, flush=True)
            time.sleep(wait)
            retries += 1

    pngFileName = '{}.{}.{}.png'.format(zoom, x, y)
    webpFileName = '{}.{}.{}.webp'.format(zoom, x, y)

    with open(pngFileName, 'wb') as f:
        f.write(response.content)
        f.close()

    subprocess.run(
        ["cwebp",
         pngFileName,
         "-z", "9",
         "-quiet",
         "-noalpha",
         "-o", webpFileName],
        check=True
    )
    newBlob = open(webpFileName, 'rb').read()
    os.remove(pngFileName)
    os.remove(webpFileName)
    return newBlob


if __name__ == '__main__':

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

    for region in regions.regions:
        fileName = 'out/'+region['continent']+'/'+region['name']+'.terrain'
        bbox = region['bbox']

        if os.path.exists(fileName):
            print("Terrain data for {} already exists. Skipping.".format(region['name']))
            continue
        print("Working on country {}.".format(region['name']))

        tmpFileName = '{}.terrain'.format(region['name'])
        dbConnection = None
        try:
            os.remove(tmpFileName)
        except BaseException as err:
            True
        dbConnection = sqlite3.connect(tmpFileName)
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE metadata (name text, value text)')
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('name', '{}')".format(
            region['continent']+'/'+region['name']))
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('type', 'baselayer')")
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('version', '{}')".format(
            date.today().strftime("%d-%b-%Y")))
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('description', 'Terrain data for Enroute Flight Navigation')")
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('format', 'webp')")
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('encoding', 'terrarium')")
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('maxzoom', ?)", (str(zoomMax),))
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('minzoom', ?)", (str(zoomMin),))
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('attribution', ?)", (attribution,))
        bboxString = str(bbox[0])+','+str(bbox[1]) + \
            ','+str(bbox[2])+','+str(bbox[3])
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('bounds', '{}')".format(bboxString))
        cursor.execute(
            "INSERT INTO metadata (name, value) VALUES ('attribution', 'None yet')")
        cursor.execute(
            'CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)')

        iterations = 0
        for zoom in range(zoomMin, zoomMax+1):
            (xmin, ymax) = deg2num(bbox[1], bbox[0], zoom)
            (xmax, ymin) = deg2num(bbox[3], bbox[2], zoom)
            iterations = iterations + (xmax+1-xmin)*(ymax+1-ymin)

        bar = pyprind.ProgBar(iterations)
        for zoom in range(zoomMin, zoomMax+1):
            (xmin, ymax) = deg2num(bbox[1], bbox[0], zoom)
            (xmax, ymin) = deg2num(bbox[3], bbox[2], zoom)
            for x in range(xmin, xmax+1):
                pool = multiprocessing.Pool(multiprocessing.cpu_count())
                webpImages = pool.starmap(
                    getWebp, [(zoom, x, y) for y in range(ymin, ymax+1)])
                pool.close()
                for y in range(ymin, ymax+1):
                    yflipped = 2**zoom-1-y
                    blob = webpImages[y-ymin]
                    cursor.execute(
                        "INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)", (zoom, x, yflipped, blob))
                bar.update(ymax+1-ymin, force_flush=True)

        dbConnection.commit()

        cursor.execute(
            "CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row)")
        dbConnection.commit()

        cursor.execute("vacuum")
        dbConnection.commit()

        cursor.close()
        dbConnection.commit()
        dbConnection.close()

        os.makedirs("out/"+region['continent'], exist_ok=True)
        os.rename(tmpFileName, fileName)
