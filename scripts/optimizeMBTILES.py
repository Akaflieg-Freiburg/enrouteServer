#!/bin/python3

import gzip
import sqlite3
import sys
import vector_tile
import vector_tile_pb2

if len(sys.argv) == 1:
    print("{} file.mbtiles".format(sys.argv[0]))
    print("Optimizes MBTILES file for enrouteFlightMap, by removing all data that is irrelevant to the map. The file is modified in-place.")
    exit(0)


# Open database
conn = sqlite3.connect(sys.argv[1])
c = conn.cursor()

#
# Go through all remaining tiles
#
for row in c.execute('SELECT * FROM tiles'):
    blob = row[3]
    unzipedBlob = gzip.decompress(blob)
    
    tile = vector_tile_pb2.Tile()
    tile.ParseFromString(unzipedBlob)

    vector_tile.optimizeTile(tile)

    newBlob = gzip.compress(tile.SerializeToString())
    localCursor = conn.cursor()
    localCursor.execute("UPDATE tiles SET tile_data=? WHERE zoom_level=? AND tile_column=? AND tile_row=?", (newBlob, row[0], row[1], row[2]))

print("Committing changes")
conn.commit()

print("Compactifying database")
c.execute("vacuum")
conn.commit()

# Close database
conn.close()
