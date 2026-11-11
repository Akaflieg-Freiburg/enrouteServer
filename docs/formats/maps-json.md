# The map index (`maps.json`)

*Audience: developers of Enroute Flight Navigation and the maintainer. This is the normative specification of the file that tells the app which data files exist on the server.*

| | |
|---|---|
| **Producer** | [`deploy-hetzner.py`](../../scripts/deploy-hetzner.py), regenerated on every deployment from the content of the staging directory |
| **Consumer** | Enroute app: `DataManagement::DataManager` |
| **Location** | `https://enroute-data.akaflieg-freiburg.de/enroute-GeoJSONv003/maps.json` (hard-coded in the app) |

The app downloads this file periodically. It uses the file to:

- list the available maps and databases under "Library / Maps and Data"
- tell the user when updates are available
- show the "What's new" message
- ask the user to update the app when the server requires a newer version

## Example

```json
{
    "maps": [
        {
            "bbox": [-8.704895, 18.92874, 12.03598, 37.77284],
            "path": "Africa/Algeria.geojson",
            "size": 288860,
            "time": "20260806"
        },
        {
            "path": "Flarm Database.txt",
            "size": 742095,
            "time": "20260909"
        }
    ],
    "minAppVersion": "2.31.8",
    "url": "https://enroute-data.akaflieg-freiburg.de/enroute-GeoJSONv003",
    "whatsNew": "Enroute Flight Navigation now offers …"
}
```

The producer writes the file with sorted keys and an indentation of four spaces.

## The top-level object

| Key | Type | Meaning |
|---|---|---|
| `url` | string | The base URL. The download URL of each file is `url + "/" + path`. |
| `maps` | array | One *map object* (see below) for every downloadable file. |
| `whatsNew` | string | An English message about recent changes in map coverage. The app shows it to the user when the text changes. An empty string means "nothing new". |
| `minAppVersion` | string | The oldest app version that can use the files on the server, in the form `major.minor.patch` (e.g. `2.31.8`). **If the running app is older, it ignores the entire `maps` array** and asks the user to update. |

## Map objects

| Key | Type | Required | Meaning |
|---|---|---|---|
| `path` | string | yes | The path of the file, relative to `url`. The app stores the file under the same relative path and rejects paths that would leave its data directory. The file extension determines the kind of data (see below). |
| `size` | integer | yes | The file size on the server, in bytes. |
| `time` | string | yes | The modification day of the file, as `YYYYMMDD`. The app offers an update when this date is newer than its local copy. |
| `bbox` | array of 4 numbers | no | The bounding box of the region, as `[lon_min, lat_min, lon_max, lat_max]` in WGS84 degrees. |

### File extensions

| Extension | Kind | Specification |
|---|---|---|
| `.geojson` | aviation map | [geojson.md](geojson.md) |
| `.mbtiles` | vector base map | [basemap.md](basemap.md) |
| `.raster` | raster chart | [raster.md](raster.md) |
| `.terrain` | elevation data | [terrain.md](terrain.md) |
| `.vac` | visual approach chart collection | [vac.md](vac.md) |
| `.txt` | database (Flarm ID database, METAR station list) | [flarm-database.md](flarm-database.md) |

### How the producer derives `bbox`

`deploy-hetzner.py` adds a `bbox` by looking for the first region in [`regions.py`](../../scripts/regions.py) whose name occurs as a substring of the file name. For example, `Europe/France ICAO Chart.raster` and `Europe/France.vac` both get the bounding box of the region "France". Files that match no region, such as the databases, have no `bbox`.

> **Known defect:** substring matching with "first match wins" assigns the wrong box when one region name contains another. Currently, the files of "Northern Ireland" receive the bounding box of "Ireland", which comes first in `regions.py` ([#71](https://github.com/Akaflieg-Freiburg/enrouteServer/issues/71)).

### Compressed copies

For `.geojson` and `.txt` files, the server also holds a zopfli-compressed copy with an extra `.gz` extension. These copies are **not** listed in `maps.json`.

## Versioning

The path component `enroute-GeoJSONv003` is the version of the server layout. A breaking change in any file format or in this file requires a new directory (`…v004`) and a matching change in the app. For changes that old apps can safely ignore, it is enough to raise `minAppVersion`.

## Changes to this specification

- **2026-11**: moved here from the GitHub wiki and rewritten from the producing code:
  - updated the server URL (the old one was `cplx.vm.uni-freiburg.de/…v001`)
  - added `minAppVersion` and `bbox`
  - documented the file extensions and the `.gz` copies
