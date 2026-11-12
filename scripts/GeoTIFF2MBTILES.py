"""
GeoTIFF2MBTILES
===============
Convert a GeoTIFF chart into an MBTiles raster file with WEBP tiles, including
the lower zoom levels. All image processing is done by GDAL.

Usage (from inside scripts/)::

    python3 GeoTIFF2MBTILES.py input.tif output.mbtiles
"""

import os
import sqlite3
import sys
from osgeo import gdal

# Version of the conversion. generateRasterMaps.py converts a cached GeoTIFF
# again when this number differs from the one used for the last conversion.
# Increase it whenever a change here alters the generated files.
VERSION = 2

# Tile edge length in pixels, at all zoom levels
TILE_SIZE = 512

# Lowest zoom level in the generated files
MIN_ZOOM = 7

def GeoTIFF2MBTILES(infile, outfile):
    """
    Convert a GeoTIFF file to an MBTiles file with WEBP tiles

    GDAL reprojects the image to Web Mercator and picks the highest zoom level
    to match the resolution of the source. The lower zoom levels, down to
    MIN_ZOOM, are then computed from the highest one. Lanczos resampling is
    used in both steps, because it keeps text and lines crisp.

    :param infile: Path of the GeoTIFF file

    :param outfile: Path of the MBTiles file to create
    """
    gdal.UseExceptions()

    # GDAL opens an MBTiles file for update only if its name ends in
    # '.mbtiles'. So work on a temporary file with that ending. This also
    # ensures that an unfinished file never appears under the name 'outfile'.
    tmpfile = outfile + '.part.mbtiles'
    if os.path.exists(tmpfile):
        os.remove(tmpfile)

    try:
        print("Converting GeoTIFF to MBTILES")
        ds = gdal.Open(infile)
        # The 'name' metadata entry is the name of 'outfile' without its
        # ending, e.g. "Switzerland ICAO Chart".
        name = os.path.splitext(os.path.basename(outfile))[0]
        translate_options = gdal.TranslateOptions(format='MBTILES', creationOptions=[
            'TILE_FORMAT=WEBP', f'BLOCKSIZE={TILE_SIZE}', 'RESAMPLING=LANCZOS', f'NAME={name}', f'DESCRIPTION={name}'])
        out_ds = gdal.Translate(tmpfile, ds, options=translate_options)
        out_ds = None  # Closes the file
        ds = None

        conn = sqlite3.connect(tmpfile)
        max_zoom = int(conn.execute("SELECT value FROM metadata WHERE name = 'maxzoom'").fetchone()[0])
        conn.close()

        # Lower zoom levels are overviews in GDAL terms. GDAL writes them as
        # tiles of the same size and updates the 'minzoom' metadata entry.
        factors = [2**n for n in range(1, max_zoom - MIN_ZOOM + 1)]
        if factors:
            print(f"Computing zoom levels {MIN_ZOOM}-{max_zoom - 1}")
            out_ds = gdal.OpenEx(tmpfile, gdal.OF_RASTER | gdal.OF_UPDATE, open_options=['TILE_FORMAT=WEBP', 'QUALITY=85'])
            out_ds.BuildOverviews('LANCZOS', factors)
            out_ds = None

        # The app reads the tile size from this entry. Without it, the app has
        # to guess the size from an arbitrary tile.
        conn = sqlite3.connect(tmpfile)
        conn.execute("INSERT INTO metadata (name, value) VALUES ('tileSize', ?)", (str(TILE_SIZE),))
        conn.commit()
        conn.close()
    except BaseException:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
        raise

    os.replace(tmpfile, outfile)

def update_mbtiles_metadata(mbtiles_path, attribution=None, description=None, version=None):
    """
    Update attribution and description fields in an MBTILES file.
    
    Args:
        mbtiles_path (str): Path to the MBTILES file
        attribution (str, optional): New attribution text
        description (str, optional): New description text
    """
    try:
        # Connect to the MBTILES file (SQLite database)
        conn = sqlite3.connect(mbtiles_path)
        cursor = conn.cursor()
        
        # Check if metadata table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='metadata'
        """)
        
        if cursor.fetchone() is None:
            raise ValueError("No metadata table found in the MBTILES file")
        
        # First, make sure the name column has a unique constraint
        cursor.execute("""
        PRAGMA table_info(metadata)
        """)
        columns_info = cursor.fetchall()
        has_primary_key = any(col[5] == 1 for col in columns_info)  # Check if any column is a primary key

        if not has_primary_key:
            # Recreate the table with a primary key if it doesn't have one
            cursor.execute("""
            CREATE TABLE metadata_new (
                name TEXT PRIMARY KEY,
                value TEXT
            )
            """)
            cursor.execute("""
            INSERT INTO metadata_new SELECT * FROM metadata
            """)
            cursor.execute("""
            DROP TABLE metadata
            """)
            cursor.execute("""
            ALTER TABLE metadata_new RENAME TO metadata
            """)

        # Update attribution if provided
        if attribution is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO metadata (name, value)
                VALUES ('attribution', ?)
            """, (attribution,))
            
        # Update description if provided
        if description is not None:
            cursor.execute("""
                INSERT OR REPLACE INTO metadata (name, value)
                VALUES ('description', ?)
            """, (description,))

        # Update version if provided
        if version is not None:
            cursor.execute("""
                REPLACE INTO metadata (name, value)
                VALUES ('version', ?)
            """, (version,))
        
        # Commit changes
        conn.commit()
        print("Metadata updated successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()
    
if __name__ == "__main__":
    # If no arguments, print help and exit
    if len(sys.argv) != 3:
        print("Convert GeoTIFF files to MBTiles format")
        print("Usage:")
        print("python GeoTIFF2MBTILES.py input.tif output.mbtiles")
        sys.exit(-1)
    GeoTIFF2MBTILES(sys.argv[1], sys.argv[2])
