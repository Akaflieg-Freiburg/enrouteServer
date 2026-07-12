#!/usr/bin/env python3
"""
MBTILES WEBP Tile Validator
Validates all WEBP tiles in an MBTILES file to detect corruption.
"""

import sqlite3
import sys
from pathlib import Path
from io import BytesIO
from PIL import Image

def validate_mbtiles(mbtiles_path, verbose=False):
    """
    Validate all WEBP tiles in an MBTILES file.
    
    Args:
        mbtiles_path: Path to the .mbtiles file
        verbose: Print details for each tile checked
    
    Returns:
        Dictionary with validation results
    """
    if not Path(mbtiles_path).exists():
        print(f"Error: File '{mbtiles_path}' not found")
        sys.exit(1)
    
    # Connect to the MBTILES database
    conn = sqlite3.connect(mbtiles_path)
    cursor = conn.cursor()
    
    # Get total tile count
    cursor.execute("SELECT COUNT(*) FROM tiles")
    total_tiles = cursor.fetchone()[0]
    
    print(f"Found {total_tiles} tiles to validate...")
    print("-" * 50)
    
    corrupt_tiles = []
    valid_tiles = 0
    
    # Fetch all tiles
    cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles")
    
    for idx, (zoom, col, row, tile_data) in enumerate(cursor.fetchall(), 1):
        tile_id = f"z{zoom}/x{col}/y{row}"
        
        try:
            # Try to open and verify the WEBP image
            img = Image.open(BytesIO(tile_data))
            
            # Verify it's actually WEBP
            if img.format != 'WEBP':
                corrupt_tiles.append({
                    'tile': tile_id,
                    'error': f'Not WEBP format (found: {img.format})'
                })
                if verbose:
                    print(f"[{idx}/{total_tiles}] ❌ {tile_id} - Wrong format: {img.format}")
                continue
            
            # Attempt to load the image data to catch any corruption
            img.load()
            img.verify()
            
            valid_tiles += 1
            if verbose:
                print(f"[{idx}/{total_tiles}] ✓ {tile_id} - OK ({img.size[0]}x{img.size[1]})")
                
        except Exception as e:
            corrupt_tiles.append({
                'tile': tile_id,
                'error': str(e)
            })
            print(f"[{idx}/{total_tiles}] ❌ {tile_id} - CORRUPT: {e}")
        
        # Progress indicator for non-verbose mode
        if not verbose and idx % 100 == 0:
            print(f"Progress: {idx}/{total_tiles} tiles checked...", end='\r')
    
    conn.close()
    
    # Print summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Total tiles:    {total_tiles}")
    print(f"Valid tiles:    {valid_tiles}")
    print(f"Corrupt tiles:  {len(corrupt_tiles)}")
    print(f"Success rate:   {(valid_tiles/total_tiles*100):.2f}%")
    
    if corrupt_tiles:
        print("\n" + "-" * 50)
        print("CORRUPT TILES DETAILS:")
        print("-" * 50)
        for tile_info in corrupt_tiles:
            print(f"{tile_info['tile']}: {tile_info['error']}")
    
    return {
        'total': total_tiles,
        'valid': valid_tiles,
        'corrupt': corrupt_tiles
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_mbtiles.py <path_to_mbtiles> [--verbose]")
        print("\nExample:")
        print("  python validate_mbtiles.py tiles.mbtiles")
        print("  python validate_mbtiles.py tiles.mbtiles --verbose")
        sys.exit(1)
    
    mbtiles_path = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    try:
        results = validate_mbtiles(mbtiles_path, verbose)
        
        # Exit with error code if corrupt tiles found
        sys.exit(1 if results['corrupt'] else 0)
        
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)