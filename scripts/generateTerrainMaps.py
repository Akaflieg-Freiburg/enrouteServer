#!/usr/bin/python3

"""
generateTerrainMaps
===================
Generate terrain data (Terrarium-encoded WEBP elevation tiles, zoom 7-10) from
the AWS Terrain Tiles and write them to out/{Continent}/{Region}.terrain.

Usage (from inside scripts/)::

    python3 generateTerrainMaps.py [filter]

The optional filter restricts the run to regions whose name or continent
contains the given string.

Finished tiles are cached in terrain_storage/, together with the ETag of the
source file. A tile is downloaded and processed again only if the server
reports that its source has changed.
"""

import math
import multiprocessing
import os
import requests
import sqlite3
import subprocess
import sys
import time
import vector_tile

import numpy

from datetime import date
from PIL import Image

import regions


# Directory where finished tiles are cached. The version number is part of the
# name: increase it whenever the tile processing in getWebp() changes (clamping,
# encoder settings, ...), so that tiles produced by the old code are ignored.
cacheDir = 'terrain_storage/v1'

# HTTP session of the current worker process, created on first use. Re-using
# the session keeps the connection to the server open between tiles.
session = None


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
    """Make sure that the cache holds a current WEBP file for the given tile

    The tile is requested from the AWS Terrain Tiles. If the cache already
    holds a WEBP file for the tile, the request is conditional (ETag of the
    source file), and the server answers "304 Not Modified" unless the source
    has changed. Otherwise, the source PNG is downloaded, all elevations below
    0 m are set to 0 m, the blue channel is set to zero, and the result is
    stored as a lossless WEBP file, together with the ETag of the source.

    :param zoom: Zoom level of the tile

    :param x: Column of the tile (XYZ scheme)

    :param y: Row of the tile (XYZ scheme)

    :returns: Name of the WEBP file in the cache

    """

    global session
    if session is None:
        session = requests.Session()

    tileDir = '{}/{}/{}'.format(cacheDir, zoom, x)
    os.makedirs(tileDir, exist_ok=True)
    webpFileName = '{}/{}.webp'.format(tileDir, y)
    etagFileName = '{}/{}.etag'.format(tileDir, y)
    tmpBaseName = '{}/{}.{}.tmp'.format(tileDir, y, os.getpid())

    headers = {}
    if os.path.exists(webpFileName) and os.path.exists(etagFileName):
        with open(etagFileName) as f:
            headers['If-None-Match'] = f.read()

    retries = 1
    success = False
    while not success:
        try:
            response = session.get(
                'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{}/{}/{}.png'.format(zoom, x, y),
                headers=headers,
                timeout=60)
            response.raise_for_status()
            success = True
        except Exception as e:
            wait = retries * 30
            print('Error! Waiting %s secs and re-trying...' % wait, flush=True)
            time.sleep(wait)
            retries += 1

    # Source unchanged: the cached file is current
    if response.status_code == 304:
        return webpFileName

    pngFileName = tmpBaseName+'.png'
    with open(pngFileName, 'wb') as f:
        f.write(response.content)

    # Keep the red and green channels, set the blue channel to zero
    img = Image.open(pngFileName)
    matrix = ( 1, 0, 0, 0,
               0, 1, 0, 0,
               0, 0, 0, 0)
    pixels = numpy.array(img.convert("RGB", matrix))

    # A red value of 128 with green 0 is 0 m MSL. Set all elevations below
    # 0 m to 0 m. This flattens the sea floor and keeps coastal tiles small.
    pixels[pixels[:, :, 0] < 128] = (128, 0, 0)
    Image.fromarray(pixels).save(pngFileName)

    # "-z 8" is lossless. It is about 20 times faster than "-z 9", and the
    # files are less than 1% larger.
    subprocess.run(
        ["cwebp",
         pngFileName,
         "-z", "8",
         "-quiet",
         "-noalpha",
         "-o", tmpBaseName+'.webp'],
        check=True
    )
    os.remove(pngFileName)

    # Write the ETag last, so that an interrupted run never leaves a WEBP file
    # with an ETag that does not belong to it.
    if os.path.exists(etagFileName):
        os.remove(etagFileName)
    os.replace(tmpBaseName+'.webp', webpFileName)
    if 'ETag' in response.headers:
        with open(tmpBaseName+'.etag', 'w') as f:
            f.write(response.headers['ETag'])
        os.replace(tmpBaseName+'.etag', etagFileName)

    return webpFileName


if __name__ == '__main__':

    myRegion = ""
    if len(sys.argv) > 1:
        myRegion = sys.argv[1]

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

    for region in [region for region in regions.regions if myRegion in region['name'] or myRegion in region['continent']]:
        fileName = 'out/'+region['continent']+'/'+region['name']+'.terrain'
        bbox = region['bbox']

        print("Working on country {}.".format(region['name']))

        tmpFileName = '{}.terrain'.format(region['name'])
        dbConnection = None
        try:
            os.remove(tmpFileName)
        except BaseException as err:
            True
        dbConnection = sqlite3.connect(tmpFileName)
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE metadata (name text, value text, UNIQUE (name))')
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
            'CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)')

        tiles = []
        for zoom in range(zoomMin, zoomMax+1):
            (xmin, ymax) = deg2num(bbox[1], bbox[0], zoom)
            (xmax, ymin) = deg2num(bbox[3], bbox[2], zoom)
            for x in range(xmin, xmax+1):
                for y in range(ymin, ymax+1):
                    tiles.append( (zoom,x,y) )
        foreignTiles = vector_tile.foreignTiles(tiles, region['country'])
        tiles = [tile for tile in tiles if tile not in foreignTiles]

        # Most of the time is spent waiting for the server, so use more
        # processes than there are CPUs.
        with multiprocessing.Pool(max(16, multiprocessing.cpu_count())) as pool:
            webpFileNames = pool.starmap(getWebp, tiles)

        for (zoom,x,y), webpFileName in zip(tiles, webpFileNames):
            yflipped = 2**zoom-1-y

            with open(webpFileName, 'rb') as f:
                blob = f.read()

            cursor.execute(
                "INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)", (zoom, x, yflipped, blob))

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
