# Visual approach chart collections (`.vac`)

*Audience: developers of Enroute Flight Navigation and contributors who add chart collections. This is the normative specification of the VAC container.*

| | |
|---|---|
| **Producer** | [`generateVACCollections.py`](../../scripts/generateVACCollections.py) using [`TripKit2VACCollection.py`](../../scripts/TripKit2VACCollection.py) |
| **Consumer** | Enroute app: [`src/fileFormats/VACCollection.cpp`](https://github.com/Akaflieg-Freiburg/enroute/blob/main/src/fileFormats/VACCollection.cpp) |
| **Server path** | `{Continent}/{Name}.vac`, e.g. `Europe/France.vac` |

A `.vac` file is an SQLite database that holds many georeferenced chart images (visual approach charts, VACs). The images are encoded on the server, so the app never has to re-encode them on the device.

## Schema (`schemaVersion` 1)

```sql
CREATE TABLE metadata (key TEXT UNIQUE NOT NULL, value TEXT);

CREATE TABLE charts (
  name           TEXT PRIMARY KEY,
  topLeftLat     REAL NOT NULL, topLeftLon     REAL NOT NULL,
  topRightLat    REAL NOT NULL, topRightLon    REAL NOT NULL,
  bottomLeftLat  REAL NOT NULL, bottomLeftLon  REAL NOT NULL,
  bottomRightLat REAL NOT NULL, bottomRightLon REAL NOT NULL,
  image          BLOB NOT NULL
);
```

### Table `metadata`

| Key | Required | Value |
|---|---|---|
| `schemaVersion` | yes | `1` |
| `name` | yes | name of the collection, e.g. `France` |
| `description` | no | e.g. `Visual approach charts for France` |
| `attribution` | no | data owner, e.g. `Service de l’Information Aéronautique (SIA)` |
| `publicationDate` | no | `yyyyMMdd` |

### Table `charts`

There is one row per chart.

- `name` is the chart name shown to the user. It is unique within the collection.
- The eight corner columns give the positions of the image corners, in WGS84 degrees. The chart need not be north-up.
- `image` is a WEBP image. The producer re-encodes images at quality 90, unless they are already WEBP.

The producer runs `VACUUM` on the file before it is deployed.

## Input format

The producer reads [TripKit](https://mpmediasoft.de/products/AIPBrowserDE/help/AIPBrowserDE%20-%20Trip-Kit-Spezifikation.html) zip archives. It uses the corner coordinates (`geoCorners`) from `charts/charts_toc.json`; `toc.json` locates the chart files. If the archive has no usable table of contents, it reads the coordinates from file names of the form `name-geo_<left>_<top>_<right>_<bottom>.<ext>`.

A change that the app cannot read requires a new `schemaVersion`.
