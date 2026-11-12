# Script reference

*Audience: contributors and the maintainer. This page has one entry per script: what it does, how to call it, what it reads and what it writes.*

Run every Python script from inside `scripts/`. Unless stated otherwise, scripts take no arguments. For the format of the output files, see [formats/](formats/README.md).

## Contents

- [Wrapper scripts (top level)](#wrapper-scripts-top-level)
- [Generators](#generators)
- [Deployment](#deployment)
- [Libraries](#libraries)
- [Setup](#setup)
- [Utilities and one-offs](#utilities-and-one-offs)

---

## Wrapper scripts (top level)

These are the maintainer's production entry points. Both stop at the first failing step (`set -e`) and end with an upload. Contributors should run the individual generators instead.

### `generateAndDeployAviationMaps.sh`

Runs, in this order:

1. `generateVACCollections.py`
2. `generateRasterMaps.py`
3. `generateWorldAviationMap.py`
4. `splitAviationMap.py`
5. `deploy-hetzner.py`

Needs `openAIP` and `SFTP_PASSWORD`.

### `generateAndDeployFLARMDB.sh`

Runs `generateFlarmDB.py`, then `deploy-hetzner.py`.

Base maps and terrain data have no wrapper; the maintainer runs them by hand when needed (see [operations](operations.md)).

---

## Generators

### `generateWorldAviationMap.py`

Builds one aviation map for the whole world.

- **Reads:** open flightmaps OFMX data for the regions listed in `OFMX.py` (current AIRAC cycle), then the complete openAIP database (airports, airspaces, navaids, reporting points).
- **Does:** removes exact duplicates and reporting points that lie less than 1 km from one already seen (open flightmaps is read first, so it wins).
- **Writes:** `worldAviationMap.geojson` (in `scripts/`; not deployed).
- **Env:** `openAIP`.

### `splitAviationMap.py [filter]`

Cuts `worldAviationMap.geojson` into one map per region from `regions.py`. Each map contains all features that intersect the region's country shape, grown by 25 km.

- **Argument:** optional substring. Only regions whose name or continent contains it are processed (`Slovenia`, `Europe`, `USA`).
- **Reads:** `worldAviationMap.geojson`, `data/ne_10m_admin_0_countries/`.
- **Writes:** `out/{Continent}/{Region}.geojson`.

### `generateBaseMaps.py [filter …]`

Builds vector base maps from OpenStreetMap. For every continent that has a selected region, it downloads the Geofabrik extract, filters it with `osmium tags-filter`, and calls `vector_tile.pbf2mbtiles` for each region (`osmium extract`, `tilemaker`, removal of foreign tiles, tile optimization). See [formats/basemap.md](formats/basemap.md).

- **Arguments:** optional substrings that filter regions by name or continent.
- **Reads:** Geofabrik continent extracts (very large: Europe alone is tens of GB), `data/`, `tilemaker/`.
- **Writes:** `out/{Continent}/{Region}.mbtiles`.
- **Tools:** `curl`, `osmium`, `tilemaker`.

### `generateTerrainMaps.py [filter]`

Builds elevation data from the AWS Terrain Tiles (Terrarium encoding), zoom 7–10. Tiles outside the region's country are skipped. See [formats/terrain.md](formats/terrain.md).

- **Argument:** optional substring that filters regions by name or continent.
- **Writes:** `out/{Continent}/{Region}.terrain`.
- **Cache:** finished tiles are kept in `terrain_storage/v1/{zoom}/{x}/{y}.webp`, each with an `.etag` file that holds the ETag of its source. On every run the script asks the server whether the source has changed (`If-None-Match`) and rebuilds only the tiles that have. Tiles shared by neighbouring regions are built once. If you change the tile processing in `getWebp()`, increase the version number in `cacheDir`.
- **Temporary files:** each `.terrain` file is built in the system's temporary directory and then moved to `out/`. Tiles are processed in memory.
- **Tools:** none.

### `generateRasterMaps.py [filter …]`

Builds raster charts from two kinds of sources:

- **GeoTIFF charts** are listed in the `maps` table at the top of the script: currently the French ICAO chart and the Swiss ICAO and glider charts.
  - They are downloaded by HTTPS or SFTP and cached in `tiff_storage/`.
  - They are converted to WEBP MBTiles by `GeoTIFF2MBTILES.py`, which needs GDAL.
  - A chart is reconverted only if the remote file is newer than the cached copy.
- **open flightmaps VFR charts** are listed in the `ofm_maps` table.
  - For the current AIRAC cycle, the script downloads the slippy-tile package of each region from the open flightmaps snapshot bucket and caches it in `ofm_storage/{airac}/`, together with an `.etag` file.
  - Cached data of older cycles is deleted after the first successful download in a new cycle.
  - Regions without tiles in this cycle (HTTP 404) are skipped.
  - The merged chart layer is converted by `SlippyTiles2MBTILES.py`.

- **Arguments:** optional substrings. Only charts whose name contains one of them are processed. Example: `python3 generateRasterMaps.py Slovenia` builds only "Slovenia VFR Chart (open flightmaps)".
- **Writes:** `out/Europe/{Chart name}.raster`.
- **Env:** `SFTP_PASSWORD` (French ICAO chart only; skipped if unset).

### `generateVACCollections.py`

Converts TripKit archives of visual approach charts into `.vac` containers, using `TripKit2VACCollection.py`. The sources are listed in the `collections` table (currently France, from mpmediasoft). A collection is rebuilt only if the remote archive is newer than the cached copy in `tripkit_storage/`. Sources may be HTTPS or SFTP; SFTP sources need `SFTP_PASSWORD`.

- **Writes:** `out/{Continent}/{Name}.vac`.

### `generateFlarmDB.py`

Merges the Flarmnet database and the Open Glider Network device database into a compact FLARM ID → registration file. See [formats/flarm-database.md](formats/flarm-database.md).

- **Writes:** `out/Flarm Database.txt`.

---

## Deployment

### `deploy-hetzner.py [force]`

Uploads everything in `out/` that has changed and regenerates `maps.json`. **Maintainer only**: it needs ssh access to the server. For the exact procedure, the safety checks and the `force` argument, see [operations.md](operations.md#what-deploy-hetznerpy-does).

---

## Libraries

These modules are imported by the generators and have no command-line interface of their own.

| Module | Purpose |
|---|---|
| [`regions.py`](../scripts/regions.py) | Registry of continents and regions; `bufferedBoundary()`. See [architecture](architecture.md#regions-regionspy). |
| [`OFMX.py`](../scripts/OFMX.py) | Reads open flightmaps OFMX files: nature reserve areas, procedures, reporting points. The list of regions is at the top of the file. `currentAirac()` returns the current AIRAC cycle. |
| [`openAIP2.py`](../scripts/openAIP2.py) | Reads the openAIP REST API (`x-openaip-api-key` header, env `openAIP`) and converts airports, airspaces, navaids and reporting points to GeoJSON features. Also simplifies geometries. |
| [`vector_tile.py`](../scripts/vector_tile.py) | Base map helpers: `pbf2mbtiles` (osmium + tilemaker), `removeForeignTiles`, `optimizeVectorTiles`, `checkTilemakerSources`. Uses `vector_tile_pb2.py`, generated from `vector_tile.proto` (the Mapbox vector tile schema). To regenerate it, run `pip install grpcio-tools` and then `python3 -m grpc_tools.protoc -I. --python_out=. vector_tile.proto` in `scripts/`. |
| [`GeoTIFF2MBTILES.py`](../scripts/GeoTIFF2MBTILES.py) | GeoTIFF → WEBP MBTiles with GDAL; computes lower zoom levels; `update_mbtiles_metadata()` is also used for open flightmaps charts. Can be run directly: `python3 GeoTIFF2MBTILES.py in.tif out.mbtiles`. |
| [`SlippyTiles2MBTILES.py`](../scripts/SlippyTiles2MBTILES.py) | open flightmaps slippy-tile zip → WEBP MBTiles. Can be run directly: `python3 SlippyTiles2MBTILES.py in.zip out.raster "Map name"`. |
| [`TripKit2VACCollection.py`](../scripts/TripKit2VACCollection.py) | TripKit zip → `.vac` SQLite container. |

---

## Setup

### `downloadData.sh`

Downloads OSM water polygons and Natural Earth data into `data/`. See [setup](setup.md#one-time-data-download).

---

## Utilities and one-offs

These scripts are not part of the production pipeline.

| Script | Purpose | Status |
|---|---|---|
| [`downloadDFS.py`](../scripts/downloadDFS.py) | Downloads the German ICAO chart 1:500,000 from the DFS tile server and writes `Germany ICAO Chart.raster` into the current directory. Options: `--output`, `--bbox`, `--source-zoom`, `--quality`, `--cache`, `--offline` (see `--help`). Tiles are cached in `dfs_storage/`. | stand-alone; the result is not deployed |
| [`verifyRasterMBTILES.py`](../scripts/verifyRasterMBTILES.py) | Checks that every tile in an MBTiles file is a valid WEBP image: `python3 verifyRasterMBTILES.py file.raster [-v]` | debugging aid |
