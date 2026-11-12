# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Server-side data pipeline for the [Enroute Flight Navigation](https://akaflieg-freiburg.github.io/enroute/) app (Akaflieg Freiburg). Python 3 and shell scripts that download aviation/geographic data, transform it into app-consumable formats (GeoJSON, MBTiles, Flarm database), and deploy the results to `enroute-data.akaflieg-freiburg.de` via rsync. Linux only. There is no build system, no test suite, and no linter — the scripts are run directly by the maintainer.

Human documentation lives in `README.md`, `CONTRIBUTING.md` and `docs/` (plain Markdown rendered by GitHub; no site build). The file-format specs in `docs/formats/` are the contract with the app. When you change what a script reads/writes/accepts or an output format, update `docs/scripts.md` or `docs/formats/` in the same change. Trust the scripts over the docs if they disagree, and fix the docs.

## Commands

All Python scripts must be run from inside `scripts/` (they use relative paths like `out/`, `../staging`, `data/`).

```bash
# Full aviation-map generation + deployment (production run)
./generateAndDeployAviationMaps.sh    # = generateVACCollections → generateRasterMaps → generateWorldAviationMap
                                      #   → splitAviationMap → deploy-hetzner

# Flarm database generation + deployment
./generateAndDeployFLARMDB.sh         # = generateFlarmDB → deploy-hetzner

# Individual steps (from scripts/)
python3 generateWorldAviationMap.py   # openAIP + open flightmaps → worldAviationMap.geojson
python3 splitAviationMap.py [Region]  # split world map into out/{Continent}/{Region}.geojson;
                                      # optional arg filters by region/continent name substring
python3 generateBaseMaps.py <Region>  # OSM extracts → vector base maps (needs osmium, tilemaker CLIs)
python3 generateTerrainMaps.py <Region>  # AWS terrarium elevation tiles → terrain MBTiles
python3 generateVACCollections.py     # TripKit zips → SQLite .vac containers
python3 deploy-hetzner.py [force]     # sync staging with server, sanity-check, upload
python3 downloadDFS.py                # DFS tile server → "Germany ICAO Chart.raster" (stand-alone, not part of
                                      # the deployed pipeline; tiles cached in scripts/dfs_storage/)

# One-time prerequisite: Natural Earth + OSM water polygon data into scripts/data/
cd scripts && ./downloadData.sh
```

### Required environment variables / external tools

- `openAIP` — openAIP API key (`x-openaip-api-key` header), needed by `openAIP2.py`.
- `SFTP_PASSWORD` — for SFTP sources in `generateRasterMaps.py` (currently only the France ICAO chart) and `generateVACCollections.py` (currently none; France is fetched via HTTPS).
- CLI tools: `osmium`, `tilemaker`, `curl`, `zopfli`, `rsync` (server uses ssh port 222).
- Python packages: `requirements.txt`, plus GDAL (`osgeo`) from the system package manager. Details in `docs/setup.md`.

## Architecture

The pipeline has two data-source modules and a chain of generators feeding a shared deploy step:

1. **Source readers**: `OFMX.py` (open flightmaps AIXM/OFMX data, per-region list hard-coded at top of file) and `openAIP2.py` (openAIP REST API). Both emit GeoJSON features in the format specified in `docs/formats/geojson.md`. OFMX provides nature reserve areas, procedures and reporting points; openAIP provides airfields, airspaces, navaids and reporting points. `generateWorldAviationMap.py` reads OFMX first, then drops exact duplicates and reporting points within 1 km of one already seen, so **open flightmaps wins** for duplicate reporting points.

2. **`regions.py`** is the central registry: the list of continents (with Geofabrik OSM URLs) and regions (name, continent, bounding box, country). Adding a new map region to the product starts here; `splitAviationMap.py`, `generateBaseMaps.py`, `generateTerrainMaps.py`, and `deploy-hetzner.py` all iterate over it. Region boundaries are country shapes from Natural Earth (`scripts/data/ne_10m_admin_0_countries`) buffered via `regions.bufferedBoundary()`.

3. **Generators** write output into `scripts/out/{Continent}/{Region}.<ext>`:
   - `generateWorldAviationMap.py` + `splitAviationMap.py` → `.geojson` aviation maps
   - `generateBaseMaps.py` → vector base maps (Geofabrik download → `osmium tags-filter` → `tilemaker`, config in `scripts/tilemaker/`)
   - `generateTerrainMaps.py` → `.terrain` elevation MBTiles (finished tiles cached in `scripts/terrain_storage/v1/` with the ETag of their source; bump the version in `cacheDir` when the tile processing changes)
   - `generateRasterMaps.py` → `.raster` raster charts: ICAO/glider GeoTIFFs (→ WEBP MBTiles via `GeoTIFF2MBTILES.py`/GDAL; source TIFFs cached in `scripts/tiff_storage/`) and open flightmaps VFR charts (per-AIRAC slippy-tile zips from the OFM snapshot bucket → WEBP MBTiles via `SlippyTiles2MBTILES.py`; zips cached in `scripts/ofm_storage/{airac}/`, older cycles deleted). Optional name-substring arguments restrict the run, e.g. `python3 generateRasterMaps.py Slovenia`.
   - `generateVACCollections.py` → `.vac` visual approach chart collections (TripKit zips via `TripKit2VACCollection.py`)
   - `generateFlarmDB.py` → Flarm ID → callsign database

4. **`deploy-hetzner.py`** rsyncs the server state into `scripts/staging/`, copies changed files from `out/` over it, regenerates `staging/maps.json` (the app's map index, including `whatsNew` text and `minAppVersion` — both hand-edited constants at the top of the script), then rsyncs staging back to the server. Safety: if any file's size changed by more than 10%, or a GeoJSON exceeds 40 MiB, it aborts and requires a human to re-run with the `force` argument. `bbox` entries are assigned by region-name substring match on the file name (longest matching region name wins, so "Northern Ireland" beats "Ireland"). GeoJSON files are compared with their `info` timestamp field neutralized, so a mere date change does not trigger a re-upload.

`vector_tile.py` / `vector_tile_pb2.py` implement Mapbox vector-tile protobuf decoding, used to post-process/verify MBTiles output.

## Conventions

- Output GeoJSON is always serialized compact and deterministic: `json.dumps(..., sort_keys=True, separators=(',', ':'))`, with a top-level `info` string containing the generation date.
- `scripts/out/` and `scripts/staging/` contain generated/synced production data; do not hand-edit them.
- Public functions in library modules (`OFMX.py`, `openAIP2.py`, `vector_tile.py`, …) use reStructuredText docstrings (`:param:`, `:returns:`). Every script starts with a module docstring stating purpose and usage.
