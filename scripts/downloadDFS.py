#!/usr/bin/env python3
"""
downloadDFS
====================================
Download the German ICAO chart 1:500,000 from the tile server of DFS Deutsche
Flugsicherung GmbH and convert it into an MBTiles raster file with WEBP tiles,
as consumed by Enroute Flight Navigation. The file is called 'Germany ICAO
Chart.raster'; Enroute Flight Navigation expects the ending 'raster' for raster
maps.

Usage (from inside scripts/, no arguments needed)::

    python3 downloadDFS.py

How the map is built
--------------------

The DFS server offers 256 px tiles for zoom levels 3-12. All levels are
nearest-neighbour samples of one source image with roughly 42 m per pixel.
Zoom 12 (24 m per pixel) is the only level that contains every source pixel;
zoom 11 already drops pixels, and the lower levels are heavily aliased. This
script therefore downloads zoom 12 only and computes everything else:

- 2x2 source tiles are stitched into one 512 px tile, stored one zoom level
  lower. This is the layout of all other raster maps of this project.
- The lower zoom levels are computed with a Lanczos filter, which gives smooth
  overviews with crisp text.
- Tiles are stored as WEBP. Tiles without transparency are stored without alpha
  channel.
- The chart reaches far beyond Germany (2.7-19.8 degrees east, 45.5-57.4 degrees
  north). Only the tiles that touch Germany, with the same 25 km margin that
  the other maps of this project use, are downloaded and stored. This needs
  the Natural Earth data in scripts/data, see downloadData.sh.

The download is throttled, in order not to strain the DFS server. Expect the
first run to take about ten minutes and to transfer about 1 GB.

Downloaded tiles are kept in a cache (dfs_storage/). A later run revalidates
them with conditional requests and transfers only the tiles that have changed,
so an interrupted run is simply resumed by starting the script again. With
--offline, the map is written from the cache alone.

The chart is copyrighted by DFS. Check the terms of use before passing the
output on to others.
"""

import argparse
import email.utils
import io
import math
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from PIL import Image
from tqdm import tqdm

TILE_URL = "https://secais.dfs.de/static-maps/icao500/tiles/{z}/{x}/{y}.png"
USER_AGENT = "enrouteServer-downloadDFS/2.0 (+https://github.com/Akaflieg-Freiburg/enrouteServer)"

MAP_NAME = "Germany ICAO Chart"
MAP_DESCRIPTION = "Germany ICAO Chart 1:500,000. For information only."
MAP_ATTRIBUTION = "DFS Deutsche Flugsicherung GmbH"

# Entry of regions.py whose buffered boundary defines the area of the map
REGION = "Germany"

# Lowest zoom level of the output file, as in the other raster maps
MIN_ZOOM = 7

SOURCE_TILE_SIZE = 256
OUTPUT_TILE_SIZE = 512

# The DFS tiles carry alpha values 253-255 in areas that are meant to be opaque.
# Alpha values of at least this size are therefore read as fully opaque.
OPAQUE_ALPHA = 250

WORKERS = 4           # Parallel downloads
REQUESTS_PER_SECOND = 25   # Upper limit, in order not to strain the server
ATTEMPTS = 5          # Attempts per tile
BACKOFF = 2.0         # Seconds to wait after the first failed attempt; doubles every time
TIMEOUT = (10, 60)    # Connect and read timeout, in seconds
CHUNK = 64            # Tiles handed to the worker threads at a time


class InvalidTile(Exception):
    """The server answered, but did not deliver a usable tile"""


class DownloadError(Exception):
    """A tile could not be downloaded, even after several attempts"""


# ---------------------------------------------------------
# Tile arithmetic
# ---------------------------------------------------------

def lonlat2tile(lon, lat, zoom):
    """Slippy tile (x, y) that contains the given coordinate"""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return min(max(x, 0), n - 1), min(max(y, 0), n - 1)


def tile2lon(x, zoom):
    """Longitude of the north-west corner of slippy tile (x, ·)"""
    return x / 2 ** zoom * 360.0 - 180.0


def tile2lat(y, zoom):
    """Latitude of the north-west corner of slippy tile (·, y)"""
    return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / 2 ** zoom))))


def tile_range(bbox, zoom):
    """Tile range (x_min, y_min, x_max, y_max) that covers a (west, south, east, north) box"""
    west, south, east, north = bbox
    x_min, y_min = lonlat2tile(west, north, zoom)
    x_max, y_max = lonlat2tile(east, south, zoom)
    return x_min, y_min, x_max, y_max


def tiles_in_bbox(bbox, zoom):
    """Set of all tiles (x, y) that touch a (west, south, east, north) box"""
    x_min, y_min, x_max, y_max = tile_range(bbox, zoom)
    return {(x, y) for x in range(x_min, x_max + 1) for y in range(y_min, y_max + 1)}


def fill_gaps(tiles):
    """
    Add the tiles that are completely enclosed by the given ones.

    :param tiles: Set of (x, y)

    :returns: The given set, plus all tiles from which the outside cannot be
        reached by moving left, right, up or down without crossing the set
    """
    x_min, x_max = min(x for x, _ in tiles) - 1, max(x for x, _ in tiles) + 1
    y_min, y_max = min(y for _, y in tiles) - 1, max(y for _, y in tiles) + 1
    outside = set()
    todo = [(x_min, y_min)]
    while todo:
        x, y = todo.pop()
        if ((x, y) in outside) or ((x, y) in tiles) or not (x_min <= x <= x_max and y_min <= y <= y_max):
            continue
        outside.add((x, y))
        todo += [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    return {(x, y) for x in range(x_min, x_max + 1) for y in range(y_min, y_max + 1)} - outside


def tiles_in_region(name, zoom):
    """
    Set of all tiles (x, y) that touch a region, including the 25 km margin
    that is used for all maps of this project. Gaps that are enclosed by the
    region, such as water between the coast and the islands, are filled.

    :param name: Name of the region, as in regions.py

    :param zoom: Zoom level

    :raises RuntimeError: If the boundary data is not available
    """
    # Imported here, because the import reads the country boundaries from
    # data/, which takes a while and is not needed when --bbox is used.
    try:
        import regions
    except Exception as error:
        raise RuntimeError(
            "Cannot read the country boundaries ({}). Run the script from inside scripts/, "
            "after ./downloadData.sh, or use --bbox.".format(error)) from error
    import shapely
    import shapely.geometry

    region = next(region for region in regions.regions if region['name'] == name)
    boundary = shapely.union_all(list(regions.bufferedBoundary(region).geometry))
    shapely.prepare(boundary)
    west, south, east, north = boundary.bounds
    return fill_gaps({
        (x, y) for x, y in tiles_in_bbox((west, south, east, north), zoom)
        if boundary.intersects(shapely.geometry.box(
            tile2lon(x, zoom), tile2lat(y + 1, zoom), tile2lon(x + 1, zoom), tile2lat(y, zoom)))
    })


# ---------------------------------------------------------
# Cache of downloaded tiles
# ---------------------------------------------------------

class TileCache:
    """
    SQLite file with the tiles as delivered by the server, plus the validators
    (ETag, Last-Modified) needed for conditional requests. Empty tiles are
    stored with data NULL.
    """

    def __init__(self, path):
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS tiles (z INTEGER, x INTEGER, y INTEGER, "
            "etag TEXT, last_modified TEXT, data BLOB, PRIMARY KEY (z, x, y))"
        )
        self.conn.commit()

    def entries(self, zoom):
        """Dictionary (x, y) -> (etag, last_modified, has_content) for a zoom level"""
        rows = self.conn.execute(
            "SELECT x, y, etag, last_modified, data IS NOT NULL FROM tiles WHERE z = ?", (zoom,))
        return {(x, y): (etag, last_modified, bool(has_content)) for x, y, etag, last_modified, has_content in rows}

    def store(self, zoom, x, y, etag, last_modified, data):
        self.conn.execute("INSERT OR REPLACE INTO tiles VALUES (?, ?, ?, ?, ?, ?)",
                          (zoom, x, y, etag, last_modified, data))

    def image(self, zoom, x, y):
        """Tile as RGBA image, or None if the tile is empty or not cached"""
        row = self.conn.execute("SELECT data FROM tiles WHERE z = ? AND x = ? AND y = ?", (zoom, x, y)).fetchone()
        if (row is None) or (row[0] is None):
            return None
        return Image.open(io.BytesIO(row[0])).convert('RGBA')

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


# ---------------------------------------------------------
# Download
# ---------------------------------------------------------

class RateLimiter:
    """Hands out time slots to the worker threads, so that requests are evenly spaced"""

    def __init__(self, rate):
        self.interval = 1.0 / rate
        self.lock = threading.Lock()
        self.next_slot = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            slot = max(self.next_slot, now)
            self.next_slot = slot + self.interval
        time.sleep(slot - now)


_rate_limiter = RateLimiter(REQUESTS_PER_SECOND)
_thread_data = threading.local()


def session():
    """One HTTP session per worker thread; sessions must not be shared between threads"""
    if not hasattr(_thread_data, 'session'):
        _thread_data.session = requests.Session()
        _thread_data.session.headers['User-Agent'] = USER_AGENT
    return _thread_data.session


def has_content(data):
    """
    Check that data is a valid tile, and tell whether it shows anything.

    The server answers requests for tiles outside of the chart with a fully
    transparent tile.

    :param data: Tile as delivered by the server

    :returns: False if the tile is fully transparent, True otherwise

    :raises InvalidTile: If data is not a complete PNG image of tile size
    """
    try:
        img = Image.open(io.BytesIO(data))
        image_format, size = img.format, img.size
    except (OSError, SyntaxError, ValueError) as error:
        raise InvalidTile("not an image: {}".format(error)) from error
    if (image_format != 'PNG') or (size != (SOURCE_TILE_SIZE, SOURCE_TILE_SIZE)):
        raise InvalidTile("unexpected image, format {}, size {}".format(image_format, size))
    try:
        # Decodes the complete image, and therefore also detects truncated files
        alpha = img.convert('RGBA').getchannel('A')
    except (OSError, SyntaxError, ValueError) as error:
        raise InvalidTile("damaged image: {}".format(error)) from error
    return alpha.getbbox() is not None


def fetch(job):
    """
    Download one tile, with retries. Runs in a worker thread.

    :param job: Tuple (zoom, x, y, etag, last_modified). The last two are the
        validators of the cached copy, or None.

    :returns: None if the cached copy is still current. Otherwise the tuple
        (etag, last_modified, data), where data is None for an empty tile.

    :raises DownloadError: If the tile could not be downloaded
    """
    zoom, x, y, etag, last_modified = job
    headers = {}
    if etag:
        headers['If-None-Match'] = etag
    elif last_modified:
        headers['If-Modified-Since'] = last_modified

    for attempt in range(1, ATTEMPTS + 1):
        try:
            _rate_limiter.wait()
            response = session().get(TILE_URL.format(z=zoom, x=x, y=y), headers=headers, timeout=TIMEOUT)
            if response.status_code == 304:
                return None
            response.raise_for_status()
            if response.status_code != 200:
                raise InvalidTile("unexpected HTTP status {}".format(response.status_code))
            data = response.content
            content = has_content(data)
            return response.headers.get('ETag'), response.headers.get('Last-Modified'), data if content else None
        except (requests.RequestException, InvalidTile) as error:
            status = getattr(getattr(error, 'response', None), 'status_code', None)
            # Client errors such as 403 or 404 will not go away by trying again
            permanent = (status is not None) and (status < 500) and (status != 429)
            if permanent or (attempt == ATTEMPTS):
                raise DownloadError("Tile {}/{}/{}: {}".format(zoom, x, y, error)) from error
            time.sleep(BACKOFF * 2 ** (attempt - 1))


def download(cache, zoom, tiles, label):
    """
    Bring the cache up to date for the given tiles.

    :param cache: TileCache

    :param zoom: Zoom level

    :param tiles: Iterable of (x, y)

    :param label: Text for the progress bar

    :returns: Tuple (tiles with content, number of tiles transferred)
    """
    tiles = sorted(tiles)
    cached = cache.entries(zoom)
    with_content = set()
    transferred = 0

    executor = ThreadPoolExecutor(max_workers=WORKERS)
    try:
        with tqdm(total=len(tiles), desc=label, unit='tile') as progress:
            # Work in chunks, so that the downloaded data never piles up in memory
            for start in range(0, len(tiles), CHUNK):
                chunk = tiles[start:start + CHUNK]
                jobs = [(zoom, x, y) + cached.get((x, y), (None, None, False))[:2] for x, y in chunk]
                for (x, y), result in zip(chunk, executor.map(fetch, jobs)):
                    if result is None:
                        content = cached[(x, y)][2]
                    else:
                        etag, last_modified, data = result
                        cache.store(zoom, x, y, etag, last_modified, data)
                        content = data is not None
                        transferred += 1
                    if content:
                        with_content.add((x, y))
                    progress.update(1)
                cache.commit()
    finally:
        # On errors and on Ctrl-C: keep what has been stored, drop what is still queued
        cache.commit()
        executor.shutdown(wait=True, cancel_futures=True)

    return with_content, transferred


# ---------------------------------------------------------
# MBTiles output
# ---------------------------------------------------------

def source_image(cache, zoom, x, y):
    """Source tile as RGBA image with cleaned alpha channel, or None if the tile is empty"""
    img = cache.image(zoom, x, y)
    if img is not None:
        img.putalpha(img.getchannel('A').point(lambda alpha: 255 if alpha >= OPAQUE_ALPHA else alpha))
    return img


def encode(img, quality):
    """Encode an RGBA image as WEBP, without alpha channel if the image is opaque"""
    output = io.BytesIO()
    if img.getchannel('A').getextrema()[0] == 255:
        # method=6 is the slowest and most thorough encoder setting
        img.convert('RGB').save(output, format='WEBP', quality=quality, method=6)
    else:
        # With transparency, method=6 takes ten times as long and saves 2%. Only
        # the few tiles at the rim of the chart are affected.
        img.save(output, format='WEBP', quality=quality, method=4)
    return output.getvalue()


def build(cache, outfile, source_zoom, content, quality):
    """
    Write the MBTiles file.

    The file is written under a temporary name and moved into place at the very
    end, so that an existing file is never replaced by an incomplete one.

    :param cache: TileCache that holds the source tiles

    :param outfile: Path of the MBTiles file to create

    :param source_zoom: Zoom level of the source tiles

    :param content: Set of (x, y) of the source tiles that have content

    :param quality: WEBP quality

    :returns: Dictionary zoom level -> number of tiles written
    """
    max_zoom = source_zoom - 1
    min_zoom = min(MIN_ZOOM, max_zoom)

    partfile = outfile + '.part'
    if os.path.exists(partfile):
        os.remove(partfile)
    conn = sqlite3.connect(partfile)
    # No journal needed: the file is discarded if anything goes wrong
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("CREATE TABLE metadata (name TEXT PRIMARY KEY, value TEXT)")
    conn.execute("CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")
    conn.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")

    tile_count = {}
    progress = tqdm(total=len({(x // 2, y // 2) for x, y in content}), desc="Writing map", unit='tile')

    def render(zoom, x, y):
        """Render and store tile (zoom, x, y) and everything below. Returns the tile image, or None."""
        if zoom == max_zoom:
            size = SOURCE_TILE_SIZE
            parts = [source_image(cache, source_zoom, 2 * x + dx, 2 * y + dy) if (2 * x + dx, 2 * y + dy) in content else None
                     for dy in (0, 1) for dx in (0, 1)]
        else:
            size = OUTPUT_TILE_SIZE
            parts = [render(zoom + 1, 2 * x + dx, 2 * y + dy) for dy in (0, 1) for dx in (0, 1)]
        if not any(parts):
            return None

        img = Image.new('RGBA', (2 * size, 2 * size))
        for index, part in enumerate(parts):
            if part:
                img.paste(part, ((index % 2) * size, (index // 2) * size))
        if zoom < max_zoom:
            # Lanczos keeps text crisper than plain averaging of 2x2 pixels, at
            # about 3% larger tiles. The filter cannot look beyond the tile, so
            # the outermost pixels differ minimally from a seamless result.
            img = img.resize((OUTPUT_TILE_SIZE, OUTPUT_TILE_SIZE), Image.Resampling.LANCZOS)
        else:
            progress.update(1)

        # MBTiles counts rows from the south (TMS)
        conn.execute("INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                     (zoom, x, 2 ** zoom - 1 - y, encode(img, quality)))
        tile_count[zoom] = tile_count.get(zoom, 0) + 1
        return img

    try:
        shift = source_zoom - min_zoom
        for x, y in sorted({(x >> shift, y >> shift) for x, y in content}):
            render(min_zoom, x, y)
            conn.commit()
        progress.close()

        xs = [x for x, _ in content]
        ys = [y for _, y in content]
        bounds = [tile2lon(min(xs), source_zoom), tile2lat(max(ys) + 1, source_zoom),
                  tile2lon(max(xs) + 1, source_zoom), tile2lat(min(ys), source_zoom)]

        # The version is the date of the newest source tile
        dates = {entry[1] for tile, entry in cache.entries(source_zoom).items() if (tile in content) and entry[1]}
        metadata = {
            'name': MAP_NAME,
            'type': 'overlay',
            'format': 'webp',
            'bounds': ','.join('{:.6f}'.format(b) for b in bounds),
            'minzoom': str(min_zoom),
            'maxzoom': str(max_zoom),
            'attribution': MAP_ATTRIBUTION,
            'description': MAP_DESCRIPTION,
        }
        if dates:
            newest = max(email.utils.parsedate_to_datetime(date) for date in dates)
            metadata['version'] = newest.strftime('%Y-%m-%d %H:%M:%S')
        conn.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", metadata.items())
        conn.commit()
        conn.close()
    except BaseException:
        progress.close()
        conn.close()
        os.remove(partfile)
        raise

    os.replace(partfile, outfile)
    return tile_count


# ---------------------------------------------------------
# Command line
# ---------------------------------------------------------

def parse_bbox(text):
    try:
        west, south, east, north = (float(value) for value in text.split(','))
    except ValueError:
        raise argparse.ArgumentTypeError("expected 'west,south,east,north', for example 8.3,49.8,9.0,50.2")
    if not (-180 <= west < east <= 180 and -85 <= south < north <= 85):
        raise argparse.ArgumentTypeError("west must be smaller than east, and south smaller than north")
    return west, south, east, north


def main():
    parser = argparse.ArgumentParser(
        description="Download the German ICAO chart 1:500,000 from DFS and write it as an MBTiles file. "
                    "All arguments are optional.")
    parser.add_argument('--output', default=MAP_NAME + '.raster',
                        help="file to write (default: '%(default)s')")
    parser.add_argument('--bbox', type=parse_bbox, metavar='W,S,E,N',
                        help="cover this area, for example 8.3,49.8,9.0,50.2 (default: Germany with a 25 km margin)")
    parser.add_argument('--source-zoom', type=int, choices=(11, 12), default=12,
                        help="zoom level to download. 12 has the full detail of the chart. "
                             "11 gives a file of about half the size, and a quarter of the download, "
                             "at visibly lower sharpness (default: %(default)s)")
    parser.add_argument('--quality', type=int, choices=range(1, 101), default=85, metavar='1-100',
                        help="WEBP quality (default: %(default)s)")
    parser.add_argument('--cache', default='dfs_storage', metavar='DIR',
                        help="directory that keeps the downloaded tiles (default: '%(default)s')")
    parser.add_argument('--offline', action='store_true',
                        help="write the map from the tiles in the cache, without contacting the server. "
                             "Useful for trying other settings after a complete download")
    args = parser.parse_args()

    zoom = args.source_zoom
    # The area is fixed in terms of output tiles. Each output tile is made of
    # 2x2 source tiles.
    if args.bbox:
        output_tiles = tiles_in_bbox(args.bbox, zoom - 1)
    else:
        output_tiles = tiles_in_region(REGION, zoom - 1)
    source_tiles = {(2 * x + dx, 2 * y + dy) for x, y in output_tiles for dx in (0, 1) for dy in (0, 1)}

    cache = TileCache(os.path.join(args.cache, 'icao500.sqlite'))
    try:
        if args.offline:
            cached = cache.entries(zoom)
            missing = len(source_tiles - cached.keys())
            if missing:
                sys.exit("Error: {} of {} tiles are not in the cache. Run the script without --offline.".format(
                    missing, len(source_tiles)))
            content = {tile for tile in source_tiles if cached[tile][2]}
            transferred = 0
        else:
            content, transferred = download(cache, zoom, source_tiles, "Downloading")
        if not content:
            sys.exit("Error: The server has no chart tiles for the requested area. "
                     "Check the --bbox argument. If the problem persists, the server layout may have changed.")
        print("{} of {} tiles have content; {} transferred, {} taken from the cache".format(
            len(content), len(source_tiles), transferred, len(source_tiles) - transferred))

        tile_count = build(cache, args.output, zoom, content, args.quality)
    finally:
        cache.close()

    print("\nWrote '{}', {:.1f} MB".format(args.output, os.path.getsize(args.output) / 1024 ** 2))
    for z in sorted(tile_count):
        print("  zoom {:2d}: {:5d} tiles".format(z, tile_count[z]))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted. Run the script again to continue.")
    except DownloadError as error:
        sys.exit("\nError: {}\nDownloaded tiles are kept. Run the script again to continue.".format(error))
    except RuntimeError as error:
        sys.exit("\nError: {}".format(error))
