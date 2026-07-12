# enroute-server

The repository contains a number of scripts to set up server for the enroute app. These are python3 and shell scripts meant to be used from the Linux command line. They have never been used on any system other than Linux.

## 1. Data-transforming scripts

### 1.1 any2GeoJSON.py

This script takes a number of files with aviation data and generates a file on GeoJSON format, suitable for use with the enroute app. The following file types are accepted as input.

* asp.aip - openAIP file in XML format, containing airspace data

* nav.aip - openAIP file in XML format, describing navaids

* wpt.aip - openAIP file in XML format, describing airfields

* aixm.xml - open flightmaps file in AIXM format

The script accepts any number of files. If competing data is found in openAIP and in open flightmaps files, the data from open flightmaps is preferred.

```shell
./any2GeoJSON.py asp.aip nav.aip wpt.aip
```

The output file is always called **test.geojson**. Existing files with that name will be overwritten.


### 1.2 flarmDB.py

This script takes a Flarmnet database in FLN format, as downloaded from [this URL](https://www.flarmnet.org/static/files/wfn/data.fln) on [this page](https://www.flarmnet.org/flarmnet/downloads/). The FLN is also used by LXNavigation / XCSoar, WinPilot, LK8000 and ClearNav.  It removes a lot of data and produces a much shorter file in the format described [here](https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/Flarmnet-data-format).


### 1.3 shrinkTiles.py

This script takes a geographic map file in MBTiles format and modifies the file in-place. It simply removes all tiles with zoom > 10 and adjusts the meta-data accordingly. This will usually reduce the file size dramatically.

```shell
./shrinkTiles.py ./europe.mbtiles
```

## 2. Setup scripts

These scripts are used by the author to setup files on a file server that is then used by the **enroute** app. These scripts make a lot of assumptions about the setof of the current home directory and are probably not universally useful.

### 2.1 serverScript.py

This script does the following.

1. Downloads aviation data files from the openAIP and open flightmaps web sites

2. Run **any2GeoJSON** on the files and stores the generated files in `/home/kebekus/Austausch/aviation_maps/{Continent}`, overwriting GeoJSON files that might already exist there. 

3. Generate a new file `/home/kebekus/Austausch/aviation_maps/maps.json`. 

4. After asking interactively for permission, it uploads all file via **rsync** to the server cplx.vm.uni-freiburg.de, where the **enroute** app expects the files.

```shell
./serverScript.py
```

### 2.2. shrinkTileSet.sh

This is a trivial shell script that the author uses to set up mbtile file for use with the **enroute** app.

1. The script takes a large number of mbtile files from the directory `/mnt/storage/mbtiles/raw`, copies them to `/mnt/storage/mbtiles/working/{Continent}/{Country}.mbtiles`. Look at the script to see what files are expected.

2. It applies the script **shrinkTiles.py** to every copy. 

3. It will then move the files to `/home/kebekus/Austausch/aviation_maps/OpenMapTiles` and delete the working directory.

```shell
./shrinkTileSet.sh
```
