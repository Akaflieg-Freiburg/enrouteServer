# How to add a raster chart

*Audience: contributors and the maintainer. This page explains how to add a new raster chart (ICAO chart, glider chart, VFR chart) to the downloadable maps.*

All raster charts are built by [`scripts/generateRasterMaps.py`](../../scripts/generateRasterMaps.py). It handles two kinds of sources. The output format is described in [formats/raster.md](../formats/raster.md).

## Before you start: the license

Publishing a chart means **redistributing** it to every app user. Check that the publisher's license allows redistribution, and whether it restricts use (e.g. "for information only, not for navigation"). Mention any restriction in the chart's `description`. Name the license in your pull request.

## A GeoTIFF chart

Add an entry to the `maps` list at the top of the script:

```python
{
    'attribution': 'Federal Office of Topography swisstopo',
    'description': 'Swiss ICAO Chart. For information only.',
    'continent': 'Europe',
    'name': 'Switzerland ICAO Chart',
    'url': 'https://data.geo.admin.ch/…/luftfahrtkarten-icao_total_50_2056.tif'
},
```

- **`name`** becomes the file name (`Europe/Switzerland ICAO Chart.raster`). It should **start with the region name from `regions.py`**, because `deploy-hetzner.py` finds the chart's bounding box by searching the file name for a region name.
- **`url`** may be `https://…` or `sftp://host/path`. The server must send a `Last-Modified` header; the file is downloaded again only when that date is newer than the cached copy in `tiff_storage/`. SFTP sources also need `'sftp_user'` and the environment variable `SFTP_PASSWORD`.
- The GeoTIFF may use any projection that GDAL understands. It is reprojected to Web Mercator.

Test it:

```bash
cd scripts
python3 generateRasterMaps.py "Switzerland ICAO"
python3 verifyRasterMBTILES.py "out/Europe/Switzerland ICAO Chart.raster"
```

If the cached TIFF in `tiff_storage/` is current and has already been converted, nothing is written to `out/`. To force a rebuild without a new download, delete `tiff_storage/{Chart name}.tiff.converted`. To force a new download as well, delete the cached TIFF.

## An open flightmaps VFR chart

If [open flightmaps](https://www.openflightmaps.org) publishes slippy tiles for a region, add a tuple to `ofm_maps`:

```python
('ljla', 'Slovenia'),
```

The first element is the open flightmaps region code, the same code that `OFMX.py` uses (e.g. `ljla` for Slovenia, `ed` for Germany). The second element must match the region's `name` in `regions.py` exactly. The chart is called `"<Name> VFR Chart (open flightmaps)"` and is rebuilt automatically every AIRAC cycle.

Test it:

```bash
cd scripts
python3 generateRasterMaps.py Slovenia
```

## Deploy (maintainer)

The new chart is uploaded by the next run of `generateAndDeployAviationMaps.sh`. Consider announcing it in `whatsNewText`.
