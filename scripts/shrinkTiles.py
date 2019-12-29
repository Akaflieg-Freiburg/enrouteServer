#!/bin/python3

import json
import sqlite3
import sys

newMaxZoom = 10


if len(sys.argv) == 1:
    print("{} file.mbtiles".format(sys.argv[0]))
    print("Delete all tiles with zoom level > {} from file.mbtiles".format(newMaxZoom))
    exit(0)


# Open database
conn = sqlite3.connect(sys.argv[1])
c = conn.cursor()

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


print("Committing changes")
conn.commit()

print("Compactifying database")
c.execute("vacuum")
conn.commit()

# Close database
conn.close()
