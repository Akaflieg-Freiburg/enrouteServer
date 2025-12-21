import argparse
import sqlite3
import math
from osgeo import gdal
from PIL import Image
import io
import sys

def get_existing_zoom_level(db_path):
    """Get the zoom level from the MBTILES metadata"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM metadata WHERE name = 'maxzoom'")
    zoom = int(cursor.fetchone()[0])
    conn.close()
    return zoom

def get_tile_bounds(db_path, zoom):
    """Get min/max x and y coordinates for tiles at given zoom level"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MIN(tile_column), MAX(tile_column), 
               MIN(tile_row), MAX(tile_row) 
        FROM tiles WHERE zoom_level = ?
    """, (zoom,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_tile_data(conn, z, x, y):
    """Get tile image data from database"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tile_data FROM tiles 
        WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?
    """, (z, x, y))
    result = cursor.fetchone()
    return result[0] if result else None

def create_lower_zoom_tile(tiles):
    """Create a tile by combining 4 higher-level tiles"""
    if not any(tiles):
        return None
        
    # Create 512x512 output image (assuming input tiles are 512x512)
    new_tile = Image.new('RGBA', (1024, 1024))
    
    # Tile arrangement in MBTILES (y increases downward):
    # (2x, 2y)     (2x+1, 2y)    <- smaller y (top)
    # (2x, 2y+1)   (2x+1, 2y+1)  <- larger y (bottom)
    # Maps to image coords:
    # 2 3  <- top (smaller y in image)
    # 0 1  <- bottom (larger y in image)
    positions = [(0, 512), (512, 512), (0, 0), (512, 0)]
    
    for i, tile_data in enumerate(tiles):
        if tile_data:
            img = Image.open(io.BytesIO(tile_data))
            # Resize to 512x512 if needed
            if img.size != (512, 512):
                img = img.resize((512, 512), Image.Resampling.LANCZOS)
            new_tile.paste(img, positions[i])
    
    # Convert directly to WebP using PIL
    output = io.BytesIO()
    new_tile.save(output, format='WEBP', quality=85)
    return output.getvalue()

def process_zoom_levels(mbtiles_path, target_zoom=7):
    """Generate lower zoom levels down to target_zoom"""
    conn = sqlite3.connect(mbtiles_path)
    cursor = conn.cursor()
    
    # Get starting zoom level
    start_zoom = get_existing_zoom_level(mbtiles_path)
    if start_zoom <= target_zoom:
        print(f"Starting zoom ({start_zoom}) is already at or below target ({target_zoom})")
        return
    
    # Process each zoom level
    for current_zoom in range(start_zoom - 1, target_zoom - 1, -1):
        print(f"Processing zoom level {current_zoom}")
        min_x, max_x, min_y, max_y = get_tile_bounds(mbtiles_path, current_zoom + 1)
        
        # Calculate parent tile coordinates
        parent_min_x = min_x // 2
        parent_max_x = max_x // 2
        parent_min_y = min_y // 2
        parent_max_y = max_y // 2
        
        for x in range(parent_min_x, parent_max_x + 1):
            for y in range(parent_min_y, parent_max_y + 1):
                # Get the four child tiles
                child_tiles = [
                    get_tile_data(conn, current_zoom + 1, x*2, y*2),
                    get_tile_data(conn, current_zoom + 1, x*2 + 1, y*2),
                    get_tile_data(conn, current_zoom + 1, x*2, y*2 + 1),
                    get_tile_data(conn, current_zoom + 1, x*2 + 1, y*2 + 1)
                ]
                
                # Create and save new tile
                new_tile_data = create_lower_zoom_tile(child_tiles)
                if new_tile_data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO tiles 
                        (zoom_level, tile_column, tile_row, tile_data) 
                        VALUES (?, ?, ?, ?)
                    """, (current_zoom, x, y, new_tile_data))
        
        # Update metadata
        cursor.execute("""
            UPDATE metadata SET value = ? 
            WHERE name = 'minzoom'
        """, (current_zoom,))
        
        conn.commit()
    
    conn.close()
    print("Processing complete")

def GeoTIFF2MBTILES(infile, outfile):
    # Open the input dataset
    gdal.UseExceptions()
    ds = gdal.Open(infile)
    
    # GDAL translate options with potential parameter name corrections
    print("Converting GeoTIFF to MBTILES")
    translate_options = gdal.TranslateOptions(format='MBTILES', creationOptions=['TILE_FORMAT=WEBP', 'BLOCKSIZE=512'])
    gdal.Translate(outfile, ds, options=translate_options)

    process_zoom_levels(outfile, target_zoom=7)

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
