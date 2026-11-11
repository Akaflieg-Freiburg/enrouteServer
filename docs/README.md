# enrouteServer documentation

*This is the index of all documentation pages. Start with the [project README](../README.md) for an overview.*

## Understand

- [Architecture](architecture.md): how the pipeline fits together, data sources, regions, directories

## Run and contribute

- [Setup](setup.md): dependencies, data download, environment variables, which steps need credentials
- [Script reference](scripts.md): every script, its arguments, inputs and outputs
- How-tos:
  - [Add a region](howto/add-region.md)
  - [Add a raster chart](howto/add-raster-chart.md)
  - [Add a VAC collection](howto/add-vac-collection.md)
- [Contributing guidelines](../CONTRIBUTING.md)

## Operate

- [Operations runbook](operations.md): production runs, deployment, safety checks, troubleshooting

## File formats (contract with the app)

- [Overview](formats/README.md)
- [`maps.json`](formats/maps-json.md): the map index
- [Aviation maps (`.geojson`)](formats/geojson.md)
- [Vector base maps (`.mbtiles`)](formats/basemap.md)
- [Raster charts (`.raster`)](formats/raster.md)
- [Terrain data (`.terrain`)](formats/terrain.md)
- [Visual approach charts (`.vac`)](formats/vac.md)
- [Flarm ID database (`.txt`)](formats/flarm-database.md)
