# enrouteServer

This repository holds the data pipeline behind the maps of [**Enroute Flight Navigation**](https://akaflieg-freiburg.github.io/enroute/), a free flight navigation app for VFR pilots developed by [Akaflieg Freiburg](https://github.com/Akaflieg-Freiburg).

The Python and shell scripts here download public aviation and geographic data, convert it into formats that the app understands, and publish the results on `enroute-data.akaflieg-freiburg.de`. That is where the app downloads its maps.

| Product | Source |
|---|---|
| Aviation maps: airspaces, airfields, navaids, reporting points, traffic circuits | [openAIP](https://www.openaip.net), [open flightmaps](https://www.openflightmaps.org) |
| Vector base maps | [OpenStreetMap](https://www.openstreetmap.org) via [Geofabrik](https://download.geofabrik.de), [Natural Earth](https://www.naturalearthdata.com) |
| Terrain data | [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) |
| Raster charts: ICAO charts, VFR charts | swisstopo, SIA, open flightmaps |
| Visual approach charts | SIA, via [mpmediasoft](https://mpmediasoft.de) TripKits |
| FLARM ID database | [Flarmnet](https://www.flarmnet.org), [Open Glider Network](http://ddb.glidernet.org) |

```mermaid
flowchart LR
    S[Public data sources] --> G[Generators<br/>scripts/generate*.py] --> O[(scripts/out/)] --> D[deploy-hetzner.py] --> SRV[Download server<br/>maps.json + files] --> A[Enroute app]
```

## Start here

- **Want to understand how it works?** Read the [architecture overview](docs/architecture.md).
- **Want to contribute code, a new region or a new chart?** Read [CONTRIBUTING.md](CONTRIBUTING.md), then [set up a working copy](docs/setup.md). The how-tos cover [adding a region](docs/howto/add-region.md), [a raster chart](docs/howto/add-raster-chart.md) and [a VAC collection](docs/howto/add-vac-collection.md).
- **Developing the app and need the file formats?** The [format specifications](docs/formats/README.md) are the contract between this repository and the app.
- **Running production?** See the [operations runbook](docs/operations.md).

All pages are listed in the [documentation index](docs/README.md).

## Quick start

Linux only. You need no server credentials to run the generators.

```bash
git clone https://github.com/Akaflieg-Freiburg/enrouteServer.git
cd enrouteServer
pip install -r requirements.txt          # plus GDAL and system tools, see docs/setup.md
cd scripts
./downloadData.sh                        # one-time: Natural Earth + OSM water polygons
python3 generateRasterMaps.py Slovenia   # build one chart into out/Europe/
```

## Missing a country, or found wrong data?

- **Wrong or missing aviation data** (an airspace, frequency or reporting point) usually comes from the upstream databases. Please correct it at [openAIP](https://www.openaip.net) or [open flightmaps](https://www.openflightmaps.org). The maps here are rebuilt from their data regularly. If the error is not upstream, [open an issue](https://github.com/Akaflieg-Freiburg/enrouteServer/issues/new/choose).
- **A new country or region** can be requested with an [issue](https://github.com/Akaflieg-Freiburg/enrouteServer/issues/new/choose). Please say how you checked that the openAIP data for that country is good enough.
- **Problems with the app itself** belong in the [app repository](https://github.com/Akaflieg-Freiburg/enroute/issues).

## License

The scripts are licensed under the [GNU General Public License v3](LICENSE). The generated data is subject to the licenses of its sources, listed above. Each output file names its source in its metadata.
