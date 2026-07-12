# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Server-side data pipeline for the [Enroute Flight Navigation](https://akaflieg-freiburg.github.io/enroute/) app (Akaflieg Freiburg). Python 3 and shell scripts that download aviation/geographic data, transform it into app-consumable formats (GeoJSON, MBTiles, Flarm database), and deploy the results to `enroute-data.akaflieg-freiburg.de` via rsync. Linux only. There is no build system, no test suite, and no linter — the scripts are run directly by the maintainer.

Note: parts of README.md are outdated (it references `any2GeoJSON.py`, `serverScript.py`, `shrinkTiles.py`, which no longer exist). Trust the scripts themselves over the README.

## Commands

All Python scripts must be run from inside `scripts/` (they use relative paths like `out/`, `../staging`, `data/`).

```bash
# Full aviation-map generation + deployment (production run)
./generateAndDeployAviationMaps.sh    # = generateRasterMaps → generateWorldAviationMap → splitAviationMap → deploy-hetzner

# Flarm database generation + deployment
./generateAndDeployFLARMDB.sh         # = generateFlarmDB → deploy-hetzner

# VAC collection generation + deployment (TripKit zips → SQLite .vac containers)
./generateAndDeployVACCollections.sh  # = generateVACCollections → deploy-hetzner

# Individual steps (from scripts/)
python3 generateWorldAviationMap.py   # openAIP + open flightmaps → worldAviationMap.geojson
python3 splitAviationMap.py [Region]  # split world map into out/{Continent}/{Region}.geojson;
                                      # optional arg filters by region/continent name substring
python3 generateBaseMaps.py <Region>  # OSM extracts → vector base maps (needs osmium, tilemaker CLIs)
python3 generateTerrainMaps.py <Region>  # AWS terrarium elevation tiles → terrain MBTiles
python3 deploy-hetzner.py [force]     # sync staging with server, sanity-check, upload

# One-time prerequisite: Natural Earth + OSM water polygon data into scripts/data/
cd scripts && ./downloadData.sh

# Sphinx API docs (published to gh-pages by .github/workflows/documentation.yml)
./buildscript-documentation.sh
```

### Required environment variables / external tools

- `openAIP` — openAIP API key (`x-openaip-api-key` header), needed by `openAIP2.py`.
- `SFTP_PASSWORD` — for fetching the France ICAO chart (`generateRasterMaps.py`) and the France VAC TripKit (`generateVACCollections.py`) via SFTP.
- CLI tools: `osmium`, `tilemaker`, `curl`, `rsync` (server uses ssh port 222).
- Python packages: geopandas, shapely, geopy, requests, paramiko, Pillow, GDAL (`osgeo`), protobuf.

## Architecture

The pipeline has two data-source modules and a chain of generators feeding a shared deploy step:

1. **Source readers**: `OFMX.py` (open flightmaps AIXM/OFMX data, per-region list hard-coded at top of file) and `openAIP2.py` (openAIP REST API). Both emit GeoJSON features in the format documented in the [project wiki](https://github.com/Akaflieg-Freiburg/enrouteServer/wiki). When both sources cover the same data, **open flightmaps (OFMX) wins** — `generateWorldAviationMap.py` reads OFMX first and drops duplicates afterwards.

2. **`regions.py`** is the central registry: the list of continents (with Geofabrik OSM URLs) and regions (name, continent, bounding box, country). Adding a new map region to the product starts here; `splitAviationMap.py`, `generateBaseMaps.py`, `generateTerrainMaps.py`, and `deploy-hetzner.py` all iterate over it. Region boundaries are country shapes from Natural Earth (`scripts/data/ne_10m_admin_0_countries`) buffered via `regions.bufferedBoundary()`.

3. **Generators** write output into `scripts/out/{Continent}/{Region}.<ext>`:
   - `generateWorldAviationMap.py` + `splitAviationMap.py` → `.geojson` aviation maps
   - `generateBaseMaps.py` → vector base maps (Geofabrik download → `osmium tags-filter` → `tilemaker`, config in `scripts/tilemaker/`)
   - `generateTerrainMaps.py` → `.terrain` elevation MBTiles
   - `generateRasterMaps.py` → `.raster` ICAO/glider raster charts (GeoTIFF → WEBP MBTiles via `GeoTIFF2MBTILES.py`/GDAL; source TIFFs cached in `scripts/tiff_storage/`)
   - `generateFlarmDB.py` → Flarm ID → callsign database

4. **`deploy-hetzner.py`** rsyncs the server state into `scripts/staging/`, copies changed files from `out/` over it, regenerates `staging/maps.json` (the app's map index, including `whatsNew` text and `minAppVersion` — both hand-edited constants at the top of the script), then rsyncs staging back to the server. Safety: if any file's size changed by more than 10%, it aborts and requires a human to re-run with the `force` argument. GeoJSON files are compared with their `info` timestamp field neutralized, so a mere date change does not trigger a re-upload.

`vector_tile.py` / `vector_tile_pb2.py` implement Mapbox vector-tile protobuf decoding, used to post-process/verify MBTiles output.

## Conventions

- Output GeoJSON is always serialized compact and deterministic: `json.dumps(..., sort_keys=True, separators=(',', ':'))`, with a top-level `info` string containing the generation date.
- `scripts/out/` and `scripts/staging/` contain generated/synced production data; do not hand-edit them.
- Public functions in `OFMX.py`, `openAIP2.py`, and `vector_tile.py` use reStructuredText docstrings — they are extracted by Sphinx autodoc into the published documentation.
