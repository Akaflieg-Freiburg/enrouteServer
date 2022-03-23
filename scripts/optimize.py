#!/bin/python3

import gzip
import json
import sqlite3
import sys
from numpy import delete
import zopfli
import vector_tile_pb2

def deleteZoomLevels(c):
    # Find out what the maximal zoom value currently is
    c.execute("select value from metadata where name='maxzoom'")
    maxzoom = c.fetchone()[0]
    print("Map currently holds images for zoom values up to {}.".format(maxzoom))

    for zoom in range(newMaxZoom + 1, int(maxzoom) + 1):
        print("Deleting images      … zoom level {}.".format(zoom))
        c.execute("delete from images where tile_id GLOB '{}*'".format(zoom))
        print("Deleting image index … zoom level {}.".format(zoom))
        c.execute("delete from map where zoom_level={}".format(zoom))

    # Update the metadata in the database.
    print("Update metadata")
    c.execute("UPDATE metadata SET value='{}' where name='maxzoom'".format(newMaxZoom))

    c.execute("select value from metadata where name='json'")
    jsonString = c.fetchone()[0]
    jsonDict = json.loads(jsonString)
    for layer in jsonDict["vector_layers"]:
        if "maxzoom" in layer:
            layer["maxzoom"] = min(layer["maxzoom"], 10)
        c.execute("UPDATE metadata SET value=? where name=?", (json.dumps(jsonDict), "json"))




newMaxZoom = 12


if len(sys.argv) == 1:
    print("{} file.mbtiles".format(sys.argv[0]))
    print("Delete all tiles with zoom level > {} from file.mbtiles".format(newMaxZoom))
    exit(0)


# Open database
conn = sqlite3.connect(sys.argv[1])
c = conn.cursor()

# Delete zoom levels
deleteZoomLevels(c)


#
# Go through all remaining tiles
#
for row in c.execute('SELECT * FROM images'):
    blob = row[1]
    unzipp = gzip.decompress(blob)
    
    data = vector_tile_pb2.Tile()
    data.ParseFromString(unzipp)

    newData = vector_tile_pb2.Tile()

    for layer in data.layers:
        if layer.name in ["boundary", "mountain_peak", "park"]:
            continue

        if layer.name == "place":
            newLayer = newData.layers.add()
            newLayer.CopyFrom(layer)
            newLayer.ClearField("features")
            for feature in layer.features:
                metaData = {}                   
                for i in range(0, len(feature.tags), 2):                 
                    metaData[layer.keys[feature.tags[i]]] = layer.values[feature.tags[i+1]]
                if metaData["class"].string_value in ["city", "town", "village"]:
                    newFeature = newLayer.features.add()
                    newFeature.CopyFrom(feature)
                    # Delete tags
                    newFeature.ClearField("tags")
                    for i in range(0, len(feature.tags), 2):
                        if layer.keys[feature.tags[i]] in ["class", "name", "name_en"]:
                            newFeature.tags.append(feature.tags[i])
                            newFeature.tags.append(feature.tags[i+1])
            # TODO: Need to remove unused TAGS
            keysInUse = []
            valuesInUse = []
            for feature in newLayer.features:
                for i in range(0, len(feature.tags), 2):
                    key = newLayer.keys[feature.tags[i]]
                    if not key in keysInUse:
                        keysInUse.append(key)
                    value = newLayer.values[feature.tags[i+1]]
                    if not value in valuesInUse:
                        valuesInUse.append(value)
            print(keysInUse)
            print(valuesInUse)
            exit(-1)
            continue


        if layer.name in ["aeroway", "landcover", "landuse", "transportation", "transportation_name", "water", "water_name", "waterway"]:
            newLayer = newData.layers.add()
            newLayer.CopyFrom(layer)
            continue

        print(layer.name)

    newBlob = gzip.compress(newData.SerializeToString())
    localCursor = conn.cursor()
    localCursor.execute("UPDATE images SET tile_data=? WHERE tile_id=?", (newBlob, row[0]))



print("Committing changes")
conn.commit()

print("Compactifying database")
c.execute("vacuum")
conn.commit()

# Close database
conn.close()
