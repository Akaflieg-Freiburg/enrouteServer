#!/bin/python3

"""
vector_tile
=======================================================================================================

Toolset to manipulate vector tiles, in the format described here:
https://github.com/mapbox/vector-tile-spec/tree/master/2.1
"""

import geopandas
import math
import gzip
import os
import sqlite3
import subprocess
import vector_tile_pb2

from datetime import date
from shapely.geometry import Polygon


def num2lonlat(xtile, ytile, zoom):
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
    """
    This method takes a list of slippy map tilenames and the name of a country,
    and returns a list of those tiles that do not intersect the country.

    https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    """
    
    result = []

    # Generate buffered region around country
    worldCountryMap = geopandas.read_file( 'data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.dbf' )
    countryGDF = worldCountryMap[worldCountryMap.SOVEREIGNT == countryName]
    if countryGDF.size == 0:
        print('Country is empty: '+countryName)
        exit(-1)
    countryGDF.set_crs("EPSG:4326")
    buffer = countryGDF.to_crs(crs=3857).buffer(20000).to_crs(crs=4326) # countryGDF.buffer(0.3).set_crs("EPSG:4326")

    for (z,x,y) in tileList:
        p = Polygon([num2lonlat(x,y,z), num2lonlat(x+1,y,z), num2lonlat(x+1,y+1,z), num2lonlat(x,y+1,z)])
        intersectionVector = buffer.intersects(p)
        if True not in intersectionVector.values:
            result.append( (z,x,y) )
    return result


def optimizeVectorTiles(filename):
    """Optimize an mbtiles file

    This method optimizes an mbtiles file, by removing data this is irrelevant
    to enrouteFlightMap. It also lowers the number of mountain peaks, removing
    all but the three highest peaks from each tile.running optimizeTile on
    every tile.

    The method also adds a few entries to the map file metadata.

    :param filename: mbtiles file. The file is modified in-place.
    """

    def optimizeTile(tile):
        """Optimize a tile

        This method optimizes a tile, by removing data this is irrelevant to
        enrouteFlightMap. It also lowers the number of mountain peaks, removing
        all but the three highest peaks from each tile.

        :param tile: Tile that is to be optimized. The tile is modified
        in-place.
        """

        def getMetaData(feature, layer):
            """Obtain meta data for a feature, as a convenient string-to-value
            dictionary

            :param feature: Feature whose meta data is to be read

            :param layer: Layer that contains the feature

            :returns: Meta data dictionary
            """
            metaData = {}
            for i in range(0, len(feature.tags), 2):
                key = layer.keys[feature.tags[i]]
                val = feature.tags[i+1]
                metaData[key] = layer.values[val]
            return metaData

        def optimizeLayer(layer):
            """Delete unused keys and values from a layer

            :param layer: Layer that is to be optimized. The layer is modified
            in-place.
            """
            keysInUse = []
            valuesInUse = []
            for feature in layer.features:
                for i in range(0, len(feature.tags), 2):
                    key = layer.keys[feature.tags[i]]
                    if key not in keysInUse:
                        keysInUse.append(key)
                    feature.tags[i] = keysInUse.index(key)
                    value = layer.values[feature.tags[i+1]]
                    if value not in valuesInUse:
                        valuesInUse.append(value)
                    feature.tags[i+1] = valuesInUse.index(value)

            del layer.keys[:]
            layer.keys.extend(keysInUse)
            del layer.values[:]
            layer.values.extend(valuesInUse)

        def removeLayers(tile, list):
            """Deletes all layers from the tile whose names are contained in
            the list.

            :param tile: Tile whose layers are deleted

            :param list: List of key layer names
            """
            newLayers = []
            for layer in tile.layers:
                if layer.name in list:
                    continue
                newLayer = vector_tile_pb2.Tile.Layer()
                newLayer.CopyFrom(layer)
                newLayers.append(newLayer)
            del tile.layers[:]
            tile.layers.extend(newLayers)

        def restrictFeatures(layer, keyName, list):
            """Delete all features from the layer, except features with meta
            data where the value for the key name is contained in the list.

            :param layer: Layer whose features are deleted

            :param keyName: Name of key

            :param list: List of values
            """
            newFeatures = []
            for feature in layer.features:
                metaData = getMetaData(feature, layer)
                sVal = metaData[keyName].string_value
                fVal = metaData[keyName].float_value
                if (sVal not in list) and (fVal not in list):
                    continue
                newFeature = vector_tile_pb2.Tile.Feature()
                newFeature.CopyFrom(feature)
                newFeatures.append(newFeature)
            del layer.features[:]
            layer.features.extend(newFeatures)

        def restrictTags(layer, list):
            """Delete all tags from all features, except feature whose key
            names are contained in the list.

            :param layer: Layer whose features are deleted

            :param list: List of key names
            """
            for feature in layer.features:
                newTags = []
                for i in range(0, len(feature.tags), 2):
                    if layer.keys[feature.tags[i]] not in list:
                        continue
                    newTags.append(feature.tags[i])
                    newTags.append(feature.tags[i+1])
                del feature.tags[:]
                feature.tags.extend(newTags)

        removeLayers(tile, [
            "aerodrome_label",
            "building",
            "housenumber",
            "park",
            "poi"
        ])

        for layer in tile.layers:
            if layer.name == "aeroway":
                optimizeLayer(layer)
                continue

            if layer.name == "boundary":
                restrictFeatures(layer, "admin_level", [2.0])
                restrictTags(layer, ["admin_level"])
                optimizeLayer(layer)
                continue

            if layer.name == "landcover":
                restrictTags(layer, ["class"])
                optimizeLayer(layer)
                continue

            if layer.name == "landuse":
                restrictTags(layer, ["class"])
                optimizeLayer(layer)
                continue

            if layer.name == "mountain_peak":
                numPeaks = 5
                if len(layer.features) > numPeaks:

                    newFeatures = []
                    for feature in layer.features:
                        newFeature = vector_tile_pb2.Tile.Feature()
                        newFeature.CopyFrom(feature)
                        newFeatures.append(newFeature)

                    def getElevation(feature):
                        metaData = getMetaData(feature, layer)
                        if "ele" in metaData:
                            return metaData["ele"].float_value
                        return -1

                    newFeatures.sort(reverse=True, key=getElevation)
                    del newFeatures[numPeaks:]
                    del layer.features[:]
                    layer.features.extend(newFeatures)

                restrictTags(layer, ["class", "name_en"])
                optimizeLayer(layer)
                continue

            if layer.name == "place":
                restrictFeatures(layer, "class", ["city", "town", "village"])
                restrictTags(layer, ["class", "name", "name_en"])
                optimizeLayer(layer)
                continue

            if layer.name == "transportation":
                restrictFeatures(
                    layer,
                    "class",
                    [
                        "aerialway",
                        "motorway",
                        "trunk",
                        "primary",
                        "secondary",
                        "rail"
                    ]
                )
                restrictTags(layer, ["class", "subclass", "network"])
                optimizeLayer(layer)
                continue

            if layer.name == "transportation_name":
                restrictFeatures(
                    layer,
                    "class",
                    ["motorway", "trunk", "primary"]
                )
                restrictTags(
                    layer,
                    [
                        "class",
                        "name",
                        "name_en",
                        "network",
                        "ref",
                        "ref_length"
                    ]
                 )
                optimizeLayer(layer)
                continue

            if layer.name == "water":
                restrictFeatures(layer, "class", ["river", "lake", "ocean"])
                restrictTags(layer, ["class"])
                optimizeLayer(layer)
                continue

            if layer.name == "water_name":
                restrictTags(layer, ["class", "name", "name_en"])
                optimizeLayer(layer)
                continue

            if layer.name == "waterway":
                restrictFeatures(layer, "class", ["stream", "river", "canal"])
                restrictTags(layer, ["class", "name", "name_en"])
                optimizeLayer(layer)
                continue

            print("Error in optimizeTile(). "
                  "Unknown layer {}".format(layer.name))
            exit(-1)

    # Open database
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    #
    # Go through all remaining tiles
    #
    for row in c.execute('SELECT * FROM tiles'):
        blob = row[3]
        unzipedBlob = gzip.decompress(blob)

        tile = vector_tile_pb2.Tile()
        tile.ParseFromString(unzipedBlob)

        optimizeTile(tile)

        newBlob = gzip.compress(tile.SerializeToString())
        localCursor = conn.cursor()
        localCursor.execute("UPDATE tiles SET tile_data=? "
                            "WHERE zoom_level=? AND tile_column=? "
                            "AND tile_row=?",
                            (newBlob, row[0], row[1], row[2]))

    c.execute("REPLACE INTO metadata VALUES (?,?)",
              (
                  'attribution',
                  '<a href="http://www.openstreetmap.org/about/" '
                  'target="_blank">&copy; OpenStreetMap contributors</a>'
              ))
    c.execute("REPLACE INTO metadata VALUES (?,?)", ('name', filename))
    c.execute("REPLACE INTO metadata VALUES (?,?)",
              ('version', date.today().strftime("%d/%m/%Y")))

    print("Committing changes")
    conn.commit()

    print("Compactifying database")
    c.execute("vacuum")
    conn.commit()

    # Close database
    conn.close()


def removeForeignTiles(filename, country):
    """
    This method removes all tiles that do not intersect the country.
    """

    dbConnection = sqlite3.connect(filename)
    cursor = dbConnection.cursor()

    tileList = [(z,x,2**z-1-y) for (z,x,y) in cursor.execute('SELECT zoom_level, tile_column, tile_row FROM tiles')]
    tilesToDelete = foreignTiles(tileList, country)

    for (z,x,y) in tilesToDelete:
        cursor.execute('DELETE FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?', (z,x,2**z-1-y))

    dbConnection.commit()
    cursor.execute("vacuum")
    cursor.close()
    dbConnection.commit()
    dbConnection.close()


def pbf2mbtiles(pbfFileName, lonNW, latNW, lonSE, latSE, mbtilesFileBaseName, country):
    """Converts openstreetmap PBF file into mbtiles

    This method converts a PBF file with openstreetmap data into an mbtiles
    file. The output contains tiles for zoom level 7--10 and it optimized for
    use with the enrouteMap style.

    The coordiante arguments specify a bounding box. The box is enlarged to fit
    zoom level 6 tile boundaries. This way, it is ensured that the output does
    not contain any half-filled tiles.

    :param pbfFileName: Name of input file

    :param latNW: latitude of NW edge of bounding box

    :param lonNW: longitude of NW edge of bounding box

    :param latSE: latitude of SE edge of bounding box

    :param lonSE: longitude of SE edge of bounding box

    :param mbtilesFileBaseName: Name of output file, without ending and without
    path. The file will be overwritten if exists.

    :param country: Country. Tiles that do not intersect this country will be
        removed.
    """

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
        Converts tile number to coordinate
        taken from
        https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon..2Flat._to_tile_numbers_2
        """
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)

    (x, y) = deg2num(latNW, lonNW, 6.0)
    (extLatNW, extLonNW) = num2deg(x, y+1, 6.0)
    (x, y) = deg2num(latSE, lonSE, 6.0)
    (extLatSE, extLonSE) = num2deg(x+1, y, 6.0)

    print('Run Osmium extract')
    subprocess.run(
        "osmium extract --bbox {},{},{},{} {} "
        "-o bboxed.pbf --overwrite".format(
            extLonNW, extLatNW, extLonSE, extLatSE, pbfFileName),
        shell=True,
        check=True,
    )

    print('Run tilemaker')
    subprocess.run(
        ["tilemaker",
        "--config", "tilemaker/config.json",
        "--process", "tilemaker/process.lua",
        "--bbox", "{},{},{},{}".format(lonNW, latNW, lonSE, latSE, mbtilesFileBaseName+".mbtiles"),
        "--input", "bboxed.pbf",
        "--output", mbtilesFileBaseName+".mbtiles"],
        check=True
    )
    os.remove("bboxed.pbf")

    print('Remove tiles that do not intersect {}'.format(country))
    removeForeignTiles(mbtilesFileBaseName+".mbtiles", country)

    print('Optimize vector tiles')
    optimizeVectorTiles(mbtilesFileBaseName+".mbtiles")
