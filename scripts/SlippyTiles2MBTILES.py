"""
SlippyTiles2MBTILES
====================================
Convert a zip archive of slippy map tiles (as published by open flightmaps) into
an MBTiles raster file with WEBP tiles, as consumed by Enroute Flight Navigation.
"""

import io
import math
import os
import re
import sqlite3
import sys
import zipfile

from PIL import Image


def tile2lon(x, z):
    """Longitude of the north-west corner of slippy tile (x, ·) at zoom z"""
    return x / 2**z * 360.0 - 180.0


def tile2lat(y, z):
    """Latitude of the north-west corner of slippy tile (·, y) at zoom z"""
    n = math.pi - 2.0 * math.pi * y / 2**z
    return math.degrees(math.atan(math.sinh(n)))


def SlippyTiles2MBTILES(zip_path, outfile, name, layer='merged', tile_size=512, min_zoom=None, quality=85):
    """
    Convert slippy tiles from a zip archive into an MBTiles file.

    The archive is expected to follow the layout of the open flightmaps
    'slippyTiles_clipped.zip' packages, i.e. entries named
    ``clip/{layer}/{tile_size}/latest/{z}/{x}/{y}.png`` with XYZ tile
    numbering. Tiles are re-encoded as WEBP and stored with TMS row numbering,
    as required by the MBTiles specification. All zoom levels present in the
    archive are taken over.

    :param zip_path: Path to the zip archive

    :param outfile: Path of the MBTiles file to create. An existing file is
        overwritten.

    :param name: Value of the 'name' metadata entry

    :param layer: Tile layer to extract ('merged', 'aero' or 'base')

    :param tile_size: Tile edge length in pixels (256 or 512)

    :param min_zoom: If set, tiles below this zoom level are ignored

    :param quality: WEBP quality

    :returns: Dictionary with keys 'minzoom', 'maxzoom', 'bounds' and 'tiles'
    """

    pattern = re.compile(r'^clip/{}/{}/latest/(\d+)/(\d+)/(\d+)\.png$'.format(re.escape(layer), tile_size))

    if os.path.exists(outfile):
        os.remove(outfile)

    conn = sqlite3.connect(outfile)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=OFF")
    cursor.execute("PRAGMA synchronous=OFF")
    cursor.execute("CREATE TABLE metadata (name TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")
    cursor.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")

    # Collect the entries, grouped by zoom level, so that the archive is read in
    # a predictable order and the database can be committed per zoom level.
    entries = {}
    with zipfile.ZipFile(zip_path) as zf:
        for entry in zf.namelist():
            m = pattern.match(entry)
            if not m:
                continue
            z, x, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if (min_zoom is not None) and (z < min_zoom):
                continue
            entries.setdefault(z, []).append((x, y, entry))

        if not entries:
            conn.close()
            raise ValueError("No tiles for layer '{}' at size {} found in {}".format(layer, tile_size, zip_path))

        tile_count = 0
        extent = {}
        for z in sorted(entries):
            print("Processing zoom level {} ({} tiles)".format(z, len(entries[z])))
            xs = [x for x, _, _ in entries[z]]
            ys = [y for _, y, _ in entries[z]]
            extent[z] = (min(xs), min(ys), max(xs), max(ys))
            for x, y, entry in entries[z]:
                img = Image.open(io.BytesIO(zf.read(entry)))
                # RGBA keeps the transparency of the clipped tile borders. Do not
                # use RGB, which would fill transparent areas with black.
                img = img.convert('RGBA')
                output = io.BytesIO()
                img.save(output, format='WEBP', quality=quality)
                cursor.execute(
                    "INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                    (z, x, 2**z - 1 - y, output.getvalue())
                )
                tile_count += 1
            conn.commit()

    min_z = min(entries)
    max_z = max(entries)
    x_min, y_min, x_max, y_max = extent[max_z]
    bounds = [tile2lon(x_min, max_z), tile2lat(y_max + 1, max_z), tile2lon(x_max + 1, max_z), tile2lat(y_min, max_z)]

    metadata = {
        'name': name,
        'type': 'overlay',
        'format': 'webp',
        'bounds': ','.join('{:.6f}'.format(b) for b in bounds),
        'minzoom': str(min_z),
        'maxzoom': str(max_z),
    }
    cursor.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", metadata.items())
    conn.commit()
    conn.close()

    print("Wrote {} tiles, zoom {}-{}, bounds {}".format(tile_count, min_z, max_z, metadata['bounds']))
    return {'minzoom': min_z, 'maxzoom': max_z, 'bounds': bounds, 'tiles': tile_count}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Convert a zip archive of slippy tiles (open flightmaps layout) to MBTiles format")
        print("Usage:")
        print("python SlippyTiles2MBTILES.py input.zip output.mbtiles \"Map name\"")
        sys.exit(-1)
    SlippyTiles2MBTILES(sys.argv[1], sys.argv[2], sys.argv[3])
