#!/usr/bin/env python3
"""
Download tiles from Germany's ICAO map server and create an MBTiles file.
Usage: python icao_downloader.py --zoom 7 --bbox 5.8,47.2,15.1,55.1 --output germany_icao.mbtiles
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path
from typing import Tuple
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import math

# Tile server URL
TILE_URL = "https://secais.dfs.de/static-maps/icao500/tiles/{z}/{x}/{y}.png"

def latlon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    """Convert latitude/longitude to tile coordinates at given zoom level."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def tile_to_latlon(x: int, y: int, zoom: int) -> Tuple[float, float]:
    """Convert tile coordinates to latitude/longitude."""
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon

def get_tile_bounds(min_lat: float, min_lon: float, max_lat: float, max_lon: float, zoom: int) -> Tuple[int, int, int, int]:
    """Get tile coordinate bounds for a geographic bounding box."""
    min_x, max_y = latlon_to_tile(min_lat, min_lon, zoom)
    max_x, min_y = latlon_to_tile(max_lat, max_lon, zoom)
    return min_x, min_y, max_x, max_y

def download_tile(z: int, x: int, y: int, session: requests.Session) -> Tuple[int, int, int, bytes, bool]:
    """Download a single tile. Returns (z, x, y, data, success)."""
    url = TILE_URL.format(z=z, x=x, y=y)
    try:
        response = session.get(url, timeout=30)
        if response.status_code == 200:
            return z, x, y, response.content, True
        else:
            return z, x, y, b"", False
    except Exception as e:
        print(f"Error downloading tile {z}/{x}/{y}: {e}", file=sys.stderr)
        return z, x, y, b"", False

def create_mbtiles(output_path: str, name: str = "Germany ICAO Map", description: str = "ICAO 500k map tiles"):
    """Create an MBTiles database with metadata."""
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            name TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tiles (
            zoom_level INTEGER,
            tile_column INTEGER,
            tile_row INTEGER,
            tile_data BLOB,
            PRIMARY KEY (zoom_level, tile_column, tile_row)
        )
    """)
    
    # Insert metadata
    metadata = {
        "name": name,
        "type": "baselayer",
        "version": "1.0",
        "description": description,
        "format": "png",
        "attribution": "DFS Deutsche Flugsicherung GmbH"
    }
    
    for key, value in metadata.items():
        cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", (key, value))
    
    conn.commit()
    return conn

def flip_y(y: int, zoom: int) -> int:
    """Convert TMS (bottom-left origin) to XYZ (top-left origin) tile coordinates."""
    return (2 ** zoom - 1) - y

def main():
    parser = argparse.ArgumentParser(description="Download ICAO map tiles and create MBTiles file")
    parser.add_argument("--zoom", type=int, nargs="+", required=True, 
                        help="Zoom level(s) to download (e.g., --zoom 7 or --zoom 6 7 8)")
    parser.add_argument("--bbox", type=str, required=True,
                        help="Bounding box as 'min_lon,min_lat,max_lon,max_lat' (e.g., '5.8,47.2,15.1,55.1' for Germany)")
    parser.add_argument("--output", type=str, default="icao_map.mbtiles",
                        help="Output MBTiles file path (default: icao_map.mbtiles)")
    parser.add_argument("--workers", type=int, default=4,
                        help="Number of parallel download workers (default: 4)")
    parser.add_argument("--delay", type=float, default=0.1,
                        help="Delay between requests in seconds (default: 0.1)")
    
    args = parser.parse_args()
    
    # Parse bounding box
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, args.bbox.split(","))
    except ValueError:
        print("Error: Invalid bounding box format. Use 'min_lon,min_lat,max_lon,max_lat'", file=sys.stderr)
        sys.exit(1)
    
    print(f"Downloading tiles for bbox: ({min_lon}, {min_lat}) to ({max_lon}, {max_lat})")
    print(f"Zoom levels: {args.zoom}")
    print(f"Output: {args.output}")
    
    # Create MBTiles database
    conn = create_mbtiles(args.output)
    cursor = conn.cursor()
    
    # Update bounds in metadata
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                   ("bounds", f"{min_lon},{min_lat},{max_lon},{max_lat}"))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                   ("minzoom", str(min(args.zoom))))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                   ("maxzoom", str(max(args.zoom))))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
                   ("center", f"{(min_lon + max_lon) / 2},{(min_lat + max_lat) / 2},{min(args.zoom)}"))
    conn.commit()
    
    session = requests.Session()
    session.headers.update({"User-Agent": "ICAO-Tile-Downloader/1.0"})
    
    total_tiles = 0
    successful_tiles = 0
    
    # Process each zoom level
    for zoom in args.zoom:
        min_x, min_y, max_x, max_y = get_tile_bounds(min_lat, min_lon, max_lat, max_lon, zoom)
        
        tiles_to_download = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tiles_to_download.append((zoom, x, y))
        
        print(f"\nZoom level {zoom}: {len(tiles_to_download)} tiles")
        total_tiles += len(tiles_to_download)
        
        # Download tiles with progress bar
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(download_tile, z, x, y, session): (z, x, y)
                for z, x, y in tiles_to_download
            }
            
            with tqdm(total=len(tiles_to_download), desc=f"Zoom {zoom}") as pbar:
                for future in as_completed(futures):
                    z, x, y, data, success = future.result()
                    
                    if success and len(data) > 0:
                        # Convert to TMS y-coordinate (MBTiles uses TMS)
                        tms_y = flip_y(y, z)
                        cursor.execute(
                            "INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                            (z, x, tms_y, data)
                        )
                        successful_tiles += 1
                    
                    pbar.update(1)
                    time.sleep(args.delay)
        
        conn.commit()
    
    conn.close()
    
    print(f"\n✓ Download complete!")
    print(f"  Total tiles attempted: {total_tiles}")
    print(f"  Successfully downloaded: {successful_tiles}")
    print(f"  Output file: {args.output}")
    print(f"  File size: {Path(args.output).stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    main()
