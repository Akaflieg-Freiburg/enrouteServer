# Terrain data (`.terrain`)

*Audience: developers of Enroute Flight Navigation and contributors. This is the specification of the elevation data files.*

| | |
|---|---|
| **Producer** | [`generateTerrainMaps.py`](../../scripts/generateTerrainMaps.py) |
| **Consumer** | Enroute app: hill shading and terrain elevation (MapLibre `raster-dem` source with `terrarium` encoding) |
| **Server path** | `{Continent}/{Region}.terrain` |

A `.terrain` file is an MBTiles SQLite database that contains elevation tiles.

## Tiles

- Source: the [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) dataset (`elevation-tiles-prod/terrarium`).
- Encoding: **Terrarium**. The elevation in meters is `(R × 256 + G + B / 256) − 32768`. The producer sets the blue channel to 0.
- Elevations below 0 m are set to 0 m (the red channel is at least 128). This flattens the sea floor and keeps coastal tiles small. As a side effect, land below sea level is also stored as 0 m.
- Images are lossless **WEBP**, 256 × 256 px, at zoom levels **7 to 10**. Tiles are stored in **TMS** row order.
- Tiles that do not intersect the region's country (plus a buffer) are omitted.

## Metadata

Table `metadata(name, value)`, with `name` unique:

| Key | Value |
|---|---|
| `name` | `{Continent}/{Region}`, e.g. `Europe/Slovenia` |
| `type` | `baselayer` |
| `version` | generation date, `dd-Mon-YYYY` |
| `description` | `Terrain data for Enroute Flight Navigation` |
| `format` | `webp` |
| `encoding` | `terrarium` |
| `minzoom`, `maxzoom` | `7`, `10` |
| `bounds` | `lon_min,lat_min,lon_max,lat_max` (the region's bounding box) |
| `attribution` | attribution text required by the elevation data providers, lines separated by `<br>` |

## Changes to this specification

- **2026-11**: corrected the description of the clamping. Elevations are clamped at 0 m, not at −127 m. The files have not changed.
- **2026-11**: the metadata table now has a unique key on `name`, and `attribution` appears only once. Before, the producer inserted a second `attribution` row with the value `None yet` ([#73](https://github.com/Akaflieg-Freiburg/enrouteServer/issues/73)).
