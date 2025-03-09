import argparse
import sqlite3
import math
from osgeo import gdal
from PIL import Image
import io

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
        
    # Create 512x512 output image (assuming input tiles are 256x256)
    new_tile = Image.new('RGBA', (512, 512))
    
    # Tile arrangement in MBTILES (y increases downward):
    # (2x, 2y)     (2x+1, 2y)    <- smaller y (top)
    # (2x, 2y+1)   (2x+1, 2y+1)  <- larger y (bottom)
    # Maps to image coords:
    # 2 3  <- top (smaller y in image)
    # 0 1  <- bottom (larger y in image)
    positions = [(0, 256), (256, 256), (0, 0), (256, 0)]
    
    for i, tile_data in enumerate(tiles):
        if tile_data:
            img = Image.open(io.BytesIO(tile_data))
            # Resize to 256x256 if needed
            if img.size != (256, 256):
                img = img.resize((256, 256), Image.Resampling.LANCZOS)
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
    translate_options = gdal.TranslateOptions(format='MBTILES', creationOptions=['TILE_FORMAT=WEBP'])
    gdal.Translate(outfile, ds, options=translate_options)

    process_zoom_levels(outfile, target_zoom=7)
