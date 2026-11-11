# File formats

*Audience: developers of Enroute Flight Navigation and contributors. These pages specify every file that this pipeline publishes and the app downloads. They are the contract between this repository and the app.*

| File | Extension | Producer | Specification |
|---|---|---|---|
| Map index | `maps.json` | `deploy-hetzner.py` | [maps-json.md](maps-json.md) |
| Aviation map | `.geojson` | `generateWorldAviationMap.py` + `splitAviationMap.py` | [geojson.md](geojson.md) |
| Vector base map | `.mbtiles` | `generateBaseMaps.py` | [basemap.md](basemap.md) |
| Raster chart | `.raster` | `generateRasterMaps.py` | [raster.md](raster.md) |
| Terrain data | `.terrain` | `generateTerrainMaps.py` | [terrain.md](terrain.md) |
| Visual approach charts | `.vac` | `generateVACCollections.py` | [vac.md](vac.md) |
| Flarm ID database | `.txt` | `generateFlarmDB.py` | [flarm-database.md](flarm-database.md) |

All files are served from `https://enroute-data.akaflieg-freiburg.de/enroute-GeoJSONv003/`.

## Changing a format

The app in users' pockets cannot be updated at the same time as the server. Before you change a format:

1. Change the specification page in the same pull request as the code.
2. Decide whether old app versions can still read the new files.
   - If they can (for example, a new optional property), mention the change in the page's "Changes" section.
   - If they cannot, coordinate with the app developers in the [enroute repository](https://github.com/Akaflieg-Freiburg/enroute). Old apps are protected either by raising `minAppVersion` in `deploy-hetzner.py` or by a new server directory. See [maps-json.md](maps-json.md#versioning).
