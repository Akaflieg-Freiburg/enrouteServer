# Raster charts (`.raster`)

*Audience: developers of Enroute Flight Navigation and contributors who add chart sources. This is the specification of the raster chart files.*

| | |
|---|---|
| **Producers** | [`generateRasterMaps.py`](../../scripts/generateRasterMaps.py) using [`GeoTIFF2MBTILES.py`](../../scripts/GeoTIFF2MBTILES.py) (GeoTIFF sources) and [`SlippyTiles2MBTILES.py`](../../scripts/SlippyTiles2MBTILES.py) (open flightmaps); stand-alone: [`downloadDFS.py`](../../scripts/downloadDFS.py) |
| **Consumer** | Enroute app: listed as a raster base map by [`DataManager.cpp`](https://github.com/Akaflieg-Freiburg/enroute/blob/main/src/dataManagement/DataManager.cpp) |
| **Server path** | `{Continent}/{Chart name}.raster`, e.g. `Europe/Switzerland ICAO Chart.raster`, `Europe/Slovenia VFR Chart (open flightmaps).raster` |

A `.raster` file is an [MBTiles 1.3](https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md) SQLite database with raster tiles. The different extension lets the app tell raster charts apart from vector base maps (`.mbtiles`).

## Tiles

- Table `tiles(zoom_level, tile_column, tile_row, tile_data)` with a unique index on `(zoom_level, tile_column, tile_row)`.
- `tile_row` uses the **TMS** scheme (row 0 is in the south), as MBTiles requires.
- `tile_data` is a **WEBP** image of **512 × 512 px**, in Web Mercator (EPSG:3857).
- The zoom range depends on the producer: 7–10 for GeoTIFF sources, 4–11 for open flightmaps. Lower zoom levels are computed from the highest one.

> **Known deviation:** in files produced from GeoTIFF sources, the computed lower zoom levels currently hold 1024 × 1024 px tiles (zoom 7–9; zoom 10 is 512 px). The code comment in `GeoTIFF2MBTILES.create_lower_zoom_tile` says that 512 px was intended ([#72](https://github.com/Akaflieg-Freiburg/enrouteServer/issues/72)).

## Metadata

Table `metadata(name, value)`:

| Key | Value |
|---|---|
| `name` | display name of the chart, e.g. `Switzerland ICAO Chart` |
| `type` | `overlay` |
| `format` | `webp` |
| `bounds` | `lon_min,lat_min,lon_max,lat_max` |
| `minzoom`, `maxzoom` | zoom range present in the file |
| `attribution` | data owner, e.g. `Federal Office of Topography swisstopo` or `open flightmaps association (OFMA)`; may contain HTML links |
| `description` | short description; for open flightmaps charts it names the AIRAC cycle and states "For information only." |
| `version` | version of the source; for GeoTIFF sources it is the `Last-Modified` time of the remote file |

## Sources and licenses

The chart sources are configured in the `maps` list (GeoTIFF) and the `ofm_maps` list (open flightmaps) at the top of `generateRasterMaps.py`. To add a chart, see [howto/add-raster-chart.md](../howto/add-raster-chart.md). Each source has its own license. Check before adding a source that redistribution is allowed, and state usage restrictions in `description` (e.g. "For information only.").
