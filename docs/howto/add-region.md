# How to add a region

*Audience: contributors and the maintainer. This page walks you through adding a new country or region to the downloadable maps.*

A "region" is one entry in [`scripts/regions.py`](../../scripts/regions.py). For each region, the pipeline produces an aviation map (`.geojson`), a base map (`.mbtiles`) and terrain data (`.terrain`). Contributors usually do steps 1–4 and open a pull request; the maintainer generates the base map and terrain data and deploys.

## 1. Check that the aviation data is good enough

Aviation data for regions outside the open flightmaps coverage comes from [openAIP](https://www.openaip.net). Before you add a region, compare the openAIP data with the official AIP of the country: airspaces, airfields, frequencies and reporting points. If the data is incomplete, improve it in openAIP first. A map with missing airspaces is worse than no map.

## 2. Find the Natural Earth country name

The `country` field must be the `SOVEREIGNT` value of the country in Natural Earth. It is often, but not always, the common English name (for example `Czechia`, `United States of America`). To list all values:

```bash
cd scripts
python3 -c "import geopandas; w = geopandas.read_file('data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.dbf'); print(sorted(w.SOVEREIGNT.unique()))"
```

Overseas territories belong to their sovereign state: Réunion and New Caledonia have `country` = `France`, the Canary Islands have `country` = `Spain`. For such regions the bounding box selects the part of the country you want.

## 3. Add the entry to `regions.py`

Add a line to the `regions` list, sorted alphabetically within its continent:

```python
{'continent': 'Asia', 'name': 'Pakistan', 'bbox': [60.84438, 23.69453, 77.04897, 37.05448], 'country': 'Pakistan'},
```

- **`continent`** must be one of the names in `continents`. It becomes the directory on the server.
- **`name`** becomes the file name (`Asia/Pakistan.geojson`) and is shown in the app. It must be unique. **Avoid names that contain, or are contained in, another region's name.** `deploy-hetzner.py` assigns bounding boxes by substring matching on file names, and gets them wrong in that case (see the [known defect](../formats/maps-json.md#how-the-producer-derives-bbox) for Ireland / Northern Ireland).
- **`bbox`** is `[lon_min, lat_min, lon_max, lat_max]`. For a whole country you can print it with:

  ```bash
  python3 -c "import geopandas; w = geopandas.read_file('data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.dbf'); print(w[w.SOVEREIGNT == 'Pakistan'].total_bounds)"
  ```

## 4. Generate and check the aviation map

```bash
cd scripts
python3 generateWorldAviationMap.py      # needs the openAIP key; skip if worldAviationMap.geojson is recent
python3 splitAviationMap.py Pakistan
```

Open `out/Asia/Pakistan.geojson` in a GIS tool (QGIS, or [geojson.io](https://geojson.io) for small files). Check that everything within the country and a margin of about 25 km is present. Features that cross this area are included in full, so large airspaces and procedures may extend much further.

Then open a pull request with the change to `regions.py`. In the description, say how you checked the data quality (step 1).

## 5. Base map and terrain data (maintainer)

```bash
cd scripts
python3 generateBaseMaps.py Pakistan     # downloads the whole continent from Geofabrik
python3 generateTerrainMaps.py Pakistan
```

## 6. Deploy (maintainer)

Update `whatsNewText` in `deploy-hetzner.py` to announce the new region, then run `python3 deploy-hetzner.py`. Check the generated `staging/maps.json`: the three new files must have the correct `bbox`.

## Regions covered by open flightmaps

If [open flightmaps](https://www.openflightmaps.org) publishes data for the region, also:

- add `["<ofm code>", "<Continent>/<Name>", "<cc>"]` to `regions` at the top of [`OFMX.py`](../../scripts/OFMX.py). Only the first field, the OFM region code (e.g. `ljla`), is used for downloads. The second is a label for log output.
- add `('<ofm code>', '<Name>')` to `ofm_maps` in [`generateRasterMaps.py`](../../scripts/generateRasterMaps.py) if open flightmaps also publishes raster charts. See [add-raster-chart.md](add-raster-chart.md).
