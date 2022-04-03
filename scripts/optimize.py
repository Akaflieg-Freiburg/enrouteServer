#!/bin/python3

import gzip
import sqlite3
import sys
import vector_tile
import vector_tile_pb2



if len(sys.argv) == 1:
    print("{} file.mbtiles".format(sys.argv[0]))
    print("Delete all tiles with zoom level > {} from file.mbtiles".format(newMaxZoom))
    exit(0)


# Open database
conn = sqlite3.connect(sys.argv[1])
c = conn.cursor()

#
# Go through all remaining tiles
#
landcoverNames = set()

for row in c.execute('SELECT * FROM tiles'):
    print("Working on tile {}/{}/{}".format(row[0],row[1],row[2]))

    blob = row[3]
    unzipp = gzip.decompress(blob)
    
    data = vector_tile_pb2.Tile()
    data.ParseFromString(unzipp)

    vector_tile.removeLayers(data, ["aerodrome_label", "building", "housenumber", "landuse", "mountain_peak", "park", "poi"])

    for layer in data.layers:
        if layer.name == "aeroway":
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "boundary":
            vector_tile.restrictFeatures(layer, "admin_level", [2.0])
            vector_tile.restrictTags(layer, ["admin_level"])
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "landcover":
            for feature in layer.features:
                metaData = vector_tile.getMetaData(feature, layer)
                landcoverNames.add(metaData["class"].string_value)

            vector_tile.restrictTags(layer, ["class"])
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "place":
            vector_tile.restrictFeatures(layer, "class", ["city", "town", "village"])
            vector_tile.restrictTags(layer, ["class", "name", "name_en"])
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "transportation":
            vector_tile.restrictFeatures(layer, "class", ["motorway", "trunk", "primary", "secondary", "rail"])
            vector_tile.restrictTags(layer, ["class", "subclass", "network"])
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "transportation_name":
            vector_tile.restrictFeatures(layer, "class", ["motorway", "trunk", "primary"])
            vector_tile.restrictTags(layer, ["class", "name", "name_en", "network", "ref", "ref_length"])
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "water":
            vector_tile.restrictFeatures(layer, "class", ["river", "lake", "ocean"])
            vector_tile.restrictTags(layer, ["class"])
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "water_name":
            vector_tile.restrictTags(layer, ["class", "name", "name_en"])
            vector_tile.optimizeLayer(layer)
            continue

        if layer.name == "waterway":
            vector_tile.restrictFeatures(layer, "class", ["stream", "river", "canal"])
            vector_tile.restrictTags(layer, ["class", "name", "name_en"])
            vector_tile.optimizeLayer(layer)
            continue

        print("Unknown layer {}".format(layer.name))
        exit(-1)

    newBlob = gzip.compress(data.SerializeToString())
    localCursor = conn.cursor()
    localCursor.execute("UPDATE tiles SET tile_data=? WHERE zoom_level=? AND tile_column=? AND tile_row=?", (newBlob, row[0], row[1], row[2]))

print(landcoverNames)
print("Committing changes")
conn.commit()

print("Compactifying database")
c.execute("vacuum")
conn.commit()

# Close database
conn.close()
