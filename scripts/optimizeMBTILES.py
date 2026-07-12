#!/usr/bin/python3

import geopandas
import math
import sqlite3

from shapely.geometry import Polygon




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

def num2deg(xtile, ytile, zoom):
    """
    This returns the NW-corner of the square. Use the function with xtile+1
    and/or ytile+1 to get the other corners. With xtile+0.5 & ytile+0.5 it will
    return the center of the tile. 

    https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Tile_numbers_to_lon./lat._2
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lon_deg, lat_deg)

def foreignTiles(tileList, countryName):
    result = []

    # Generate buffered region around country
    worldCountryMap = geopandas.read_file( 'data/ne_10m_admin_0_countries.dbf' )
    countryGDF = worldCountryMap[worldCountryMap.SOVEREIGNT == countryName]
    if countryGDF.size == 0:
        print('Country is empty: '+countryName)
        exit(-1)
    countryGDF.set_crs("EPSG:4326")
    buffer = countryGDF.buffer(0.3).set_crs("EPSG:4326")

    for (z,x,y) in tileList:
#        yflipped = 2**z-1-y
        p = Polygon([num2deg(x,y,z), num2deg(x+1,y,z), num2deg(x+1,y+1,z), num2deg(x,y+1,z)])
        intersectionVector = buffer.intersects(p)
        if True not in intersectionVector.values:
            result.append( (z,x,y) )

    return result


country = 'Germany'

dbConnection = sqlite3.connect('Germany.mbtiles')
cursor = dbConnection.cursor()

tileList = [(z,x,2**z-1-y) for (z,x,y) in cursor.execute('SELECT zoom_level, tile_column, tile_row FROM tiles')]
tilesToDelete = foreignTiles(tileList, country)

for (z,x,y) in tilesToDelete:
    print(z,x,y)
    cursor.execute('DELETE FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?', (z,x,2**z-1-y))

dbConnection.commit()
cursor.execute("vacuum")
cursor.close()
dbConnection.commit()
dbConnection.close()
