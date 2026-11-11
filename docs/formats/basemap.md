# Vector base maps (`.mbtiles`)

*Audience: developers of Enroute Flight Navigation (map styling) and contributors who work on base map generation.*

| | |
|---|---|
| **Producer** | [`generateBaseMaps.py`](../../scripts/generateBaseMaps.py) using [`vector_tile.py`](../../scripts/vector_tile.py) and the tilemaker configuration in [`scripts/tilemaker/`](../../scripts/tilemaker/) |
| **Consumer** | Enroute app: MapLibre style `src/flightMap/osm-liberty.json` (and its dark variant) |
| **Server path** | `{Continent}/{Region}.mbtiles` |

A base map is an [MBTiles](https://github.com/mapbox/mbtiles-spec) file with gzip-compressed [Mapbox Vector Tiles](https://github.com/mapbox/vector-tile-spec) (`format` = `pbf`). The layers follow the [OpenMapTiles schema](https://openmaptiles.org/schema/), as produced by tilemaker. The pipeline then reduces the tiles to what the app draws.

## How a base map is made

1. Download the Geofabrik extract of the continent (`regions.continents`).
2. Run `osmium tags-filter` to keep only relevant tags: aeroways, country borders (`admin_level=2`), major roads, land use, natural features, places, railways, water and waterways, aerial ways.
3. Run `osmium extract` on the region's bounding box.
4. Run `tilemaker` with `scripts/tilemaker/config.json` and `process.lua`. This also reads OSM water polygons and Natural Earth data from `scripts/data/` (see [setup](../setup.md#one-time-data-download)).
5. Remove tiles that do not intersect the region's country (`vector_tile.removeForeignTiles`).
6. Optimize each tile (`vector_tile.optimizeVectorTiles`): drop unused layers and tags, and keep only the highest mountain peaks per tile.

## Tiles

- Zoom levels **6 to 10**.
- Layers in the final file: `aeroway`, `boundary` (`admin_level` 2 only), `landcover`, `landuse`, `mountain_peak`, `place`, `transportation`, `transportation_name`, `water`, `water_name`, `waterway`.
- The layers `aerodrome_label`, `building`, `housenumber`, `park` and `poi` are dropped. The optimizer stops with an error on any layer it does not know. If you add a layer to the tilemaker configuration, you must also handle it in `optimizeVectorTiles`.

## Metadata

| Key | Value |
|---|---|
| `name` | file name, e.g. `Slovenia.mbtiles` |
| `type` | `baselayer` |
| `format` | `pbf` |
| `description` | `Base map for Enroute Flight Navigation` |
| `minzoom`, `maxzoom` | `6`, `10` |
| `bounds`, `center` | from the region's bounding box |
| `json` | TileJSON `vector_layers` description, written by tilemaker |
| `attribution` | link to © OpenStreetMap contributors |
| `version` | generation date, `dd/mm/YYYY` |
