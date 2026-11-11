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
- Elevations below about −127 m are clamped (the red channel is at least 128).
- Images are lossless **WEBP**, 256 × 256 px, at zoom levels **7 to 10**. Tiles are stored in **TMS** row order.
- Tiles that do not intersect the region's country (plus a buffer) are omitted.

## Metadata

Table `metadata(name, value)`:

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

> **Known deviation:** the metadata table has no unique key. The producer inserts `attribution` twice, the second time with the value `None yet`.
