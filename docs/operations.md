# Operations runbook

*Audience: the maintainer, and anyone who takes over. This page explains how the production data is generated and published, and what to do when something goes wrong.*

## Overview

| What | How | When |
|---|---|---|
| Aviation maps, raster charts, VAC collections | `./generateAndDeployAviationMaps.sh` | regularly. open flightmaps publishes new data and charts every AIRAC cycle (28 days), so run at least once per cycle. |
| Flarm database | `./generateAndDeployFLARMDB.sh` | occasionally |
| Base maps | `cd scripts && python3 generateBaseMaps.py [filter]`, then `python3 deploy-hetzner.py` | when OSM data or the tilemaker configuration has changed noticeably, or for new regions |
| Terrain data | `cd scripts && python3 generateTerrainMaps.py [filter]`, then `python3 deploy-hetzner.py` | for new regions |

Before running, set `openAIP` and `SFTP_PASSWORD` (see [setup](setup.md#environment-variables)). The ssh key for `akafli@www595.your-server.de` (port 222) must be loaded.

## The server

- Public base URL: `https://enroute-data.akaflieg-freiburg.de/enroute-GeoJSONv003/`
- ssh/rsync target: `akafli@www595.your-server.de:public_html/enroute-data/enroute-GeoJSONv003/`, port 222
- The app has the URL of `maps.json` hard-coded. Changing the directory name (`…v003`) needs a new app release.

## What `deploy-hetzner.py` does

1. **Pull.** `rsync --delete` from the server into `scripts/staging/`. Staging now mirrors the server exactly.
2. **Check** every file in `out/` (`.geojson`, `.mbtiles`, `.terrain`, `.raster`, `.vac`, `.txt`). Nothing is modified in this pass. A file is an *offender* if:
   - it is a GeoJSON file larger than **40 MiB**. Larger files overwhelm the app on mobile devices.
   - its size differs from the deployed version by more than **10 %**.

   If there is at least one offender, the script lists all of them and **exits without changing anything**, unless `force` is given on the command line.
3. **Detect changes.**
   - GeoJSON is compared as parsed JSON with the `info` field ignored, so a new generation date alone is not a change.
   - `.txt` files are compared without their first line.
   - All other files are compared byte by byte.
4. **Stage.** Changed files are *moved* from `out/` to `staging/`. GeoJSON and `.txt` files are also compressed with `zopfli --best` into a `.gz` copy. Unchanged files are *deleted* from `out/`. After a successful run, `out/` is therefore empty of deployable files.
5. **Write `maps.json`** for everything in staging, including the hand-edited constants `whatsNewText` and `minAppVersion`. See [formats/maps-json.md](formats/maps-json.md).
6. **Push.** `rsync --delete` from staging to the server.

### When the sanity check fails

Look at each offender before you force anything:

- A **shrunk aviation map** usually means that a source returned incomplete data. Failed downloads do not cause this: the source readers abort on HTTP errors, and the wrapper stops before deploying. Compare the new file with the deployed one in `staging/`. If the upstream data is fine, re-run the generator later.
- A **grown or shrunk map with a known cause** (a new data source, a region whose borders were changed on purpose) is fine. Re-run with `python3 deploy-hetzner.py force`.
- A **GeoJSON over 40 MiB** must not be deployed. Split the region in `regions.py` (as was done for the USA: `USA Midwest`, `USA Northeast`, …), or simplify the data.

Since the check runs before anything is modified, you can simply fix the problem and run the deploy step again.

## Editing `whatsNew` and `minAppVersion`

Both are constants at the top of [`scripts/deploy-hetzner.py`](../scripts/deploy-hetzner.py).

- **`whatsNewText`**: an English sentence or two about new coverage, shown to users when the text changes. Update it when you add regions or products, and commit the change.
- **`minAppVersion`**: an app older than this version **ignores the whole map list** and asks the user to update. Raise it only when old apps would misbehave with the current files. Raising it cuts off all users who have not updated yet.

## Removing a file from the server

Deleting a file in `staging/` has no effect, because the next deployment first pulls the server state with `--delete`. To withdraw a region or chart:

1. Remove its source: the entry in `regions.py`, `generateRasterMaps.py` or `generateVACCollections.py`.
2. Delete the file on the server (for `.geojson` and `.txt` files, also its `.gz` copy), e.g. with `sftp -P 222 akafli@www595.your-server.de`.
3. Run `deploy-hetzner.py`. The new `maps.json` no longer lists the file, and the app no longer offers it for download.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `KeyError: 'openAIP'` | environment variable `openAIP` not set |
| "SFTP_PASSWORD environment variable not set. Skipping" | expected without the password; the French ICAO chart is not rebuilt |
| `Error in bufferedBoundary(), country is empty` | the `country` of a region in `regions.py` is not a `SOVEREIGNT` value in Natural Earth |
| error while reading `data/ne_10m_admin_0_countries/…` or other files in `data/` | run `./downloadData.sh` in `scripts/` |
| `Unknown layer …` from `optimizeVectorTiles` | a layer was added to `tilemaker/config.json` but not to `vector_tile.optimizeVectorTiles` |
| "No download needed, but the cached file needs to be converted." | the last conversion of that GeoTIFF chart did not finish, or `VERSION` in `GeoTIFF2MBTILES.py` has changed; the chart is rebuilt from the cached TIFF |
| "Conversion error occurred: …" for a GeoTIFF chart | GDAL could not convert the cached TIFF; the deployed chart stays online and the conversion is tried again on the next run. If the TIFF is damaged, delete it from `tiff_storage/` |
| "OFM: no raster tiles for … in cycle …" | open flightmaps has not published charts for that region in this cycle; the previously deployed chart stays online |
| rsync asks for a password or fails | ssh key not loaded, or port 222 blocked |
