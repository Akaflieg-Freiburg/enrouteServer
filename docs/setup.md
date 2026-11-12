# Setting up a working copy

*Audience: contributors and the maintainer. This page explains how to prepare a Linux machine so that you can run the generators locally.*

The scripts have only been used on Linux. You do **not** need any server credentials to run the generators and inspect their output. Only the upload (`deploy-hetzner.py`) and one chart source are restricted to the maintainer; see [Credentials](#credentials).

## Python packages

Python 3 is required. Install the Python dependencies:

```bash
pip install -r requirements.txt
```

`generateRasterMaps.py` also needs GDAL's Python bindings (`osgeo`). They must match the system GDAL library, so install them with the system package manager (Fedora and Debian: `python3-gdal`). If you use a virtual environment, create it with `--system-site-packages` so that it can see them.

## Command-line tools

| Tool | Needed by | Package (Fedora / Debian) |
|---|---|---|
| `osmium` | `generateBaseMaps.py` | `osmium-tool` / `osmium-tool` |
| `tilemaker` ≥ 3.0 | `generateBaseMaps.py` | build from [source](https://github.com/systemed/tilemaker) if your distribution has no recent package |
| `curl` | `generateBaseMaps.py` | `curl` |
| `wget`, `unzip` | `downloadData.sh` | `wget`, `unzip` |
| `cwebp` | `generateTerrainMaps.py` | `libwebp-tools` / `webp` |
| `zopfli` | `deploy-hetzner.py` | `zopfli` |
| `rsync`, `ssh` | `deploy-hetzner.py` | `rsync`, `openssh-clients` / `openssh-client` |
| `sqlite3` (optional) | inspecting output files | `sqlite` / `sqlite3` |

## One-time data download

Base maps, region splitting and every script that imports `regions.py` need Natural Earth country shapes and OSM water polygons in `scripts/data/`. Download them once (about 1.3 GB on disk):

```bash
cd scripts
./downloadData.sh
```

The script downloads into `data.new/` and replaces `data/` only after everything has succeeded. At the end it checks that tilemaker finds all its data sources. Re-run it now and then to pick up new Natural Earth releases.

## Environment variables

| Variable | Needed by | How to get it |
|---|---|---|
| `openAIP` | `generateWorldAviationMap.py` (through `openAIP2.py`) | Create a free account at [openaip.net](https://www.openaip.net) and generate an API client key. |
| `SFTP_PASSWORD` | `generateRasterMaps.py`, for the French ICAO chart only | Maintainer only. Without it the script skips that chart and processes all others. |

```bash
export openAIP=<your key>
```

## Credentials

| Step | Without credentials? |
|---|---|
| Aviation maps (`generateWorldAviationMap.py`, `splitAviationMap.py`) | yes, with your own free openAIP key |
| Base maps, terrain data, Flarm database | yes |
| Raster charts | yes, except the French ICAO chart |
| VAC collections | yes |
| Upload (`deploy-hetzner.py`) | **no**: needs the maintainer's ssh key for the server. Do not run it. |

## Smoke test

After setup, the quickest check that does not need the openAIP key:

```bash
cd scripts
python3 generateRasterMaps.py Slovenia        # one open flightmaps chart (needs GDAL, see above)
sqlite3 "out/Europe/Slovenia VFR Chart (open flightmaps).raster" "select * from metadata"
```

If `out/` stays empty, the chart's source is already cached and unchanged. Delete `ofm_storage/` to force a rebuild.

To test the aviation map pipeline for one region:

```bash
cd scripts
python3 generateWorldAviationMap.py   # downloads all openAIP and open flightmaps data; takes a while
python3 splitAviationMap.py Slovenia
```

Continue with the [script reference](scripts.md).
