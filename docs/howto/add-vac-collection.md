# How to add a VAC collection

*Audience: contributors and the maintainer. This page explains how to publish a new collection of visual approach charts (VACs).*

VAC collections are built by [`scripts/generateVACCollections.py`](../../scripts/generateVACCollections.py) from [TripKit](https://mpmediasoft.de/products/AIPBrowserDE/help/AIPBrowserDE%20-%20Trip-Kit-Spezifikation.html) zip archives of georeferenced charts. The output format is described in [formats/vac.md](../formats/vac.md).

## Before you start: the license

The charts are usually published by a national aeronautical information service. Check that their license allows redistribution, and give proper attribution.

## Add the collection

Add an entry to the `collections` list at the top of the script:

```python
{
    'attribution': 'Service de l’Information Aéronautique (SIA)',
    'description': 'Visual approach charts for France',
    'continent': 'Europe',
    'name': 'France',
    'url': 'https://mpmediasoft.de/OpenData/AIPBrowserWW/FR/TripKits/AIP-VFR-France-Enroute.zip'
},
```

- **`name`** becomes the file name (`Europe/France.vac`) and should be the region name from `regions.py`, so that the deploy step can attach the region's bounding box.
- **`url`** may be `https://…` (the server must send `Last-Modified`) or `sftp://…` (then add `'sftp_user'` and set `SFTP_PASSWORD`). The collection is rebuilt only when the remote archive is newer than the cached copy in `tripkit_storage/`.

## Test

```bash
cd scripts
python3 generateVACCollections.py
sqlite3 out/Europe/France.vac "select * from metadata; select count(*) from charts;"
```

Every chart needs valid corner coordinates. The converter reads them from `charts/charts_toc.json` (`geoCorners`). Only if the archive has no usable table of contents does it fall back to coordinates in the file names. Charts with invalid coordinates are skipped.

If `out/` stays empty, the archive in `tripkit_storage/` is current. Delete it to force a rebuild.

## Deploy (maintainer)

The collection is uploaded by the next run of `generateAndDeployAviationMaps.sh`.
