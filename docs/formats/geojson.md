# Aviation maps (`.geojson`)

*Audience: developers of Enroute Flight Navigation and contributors to the source readers. This is the normative specification of the aviation map files.*

| | |
|---|---|
| **Producer** | [`generateWorldAviationMap.py`](../../scripts/generateWorldAviationMap.py) (with the source readers [`OFMX.py`](../../scripts/OFMX.py) and [`openAIP2.py`](../../scripts/openAIP2.py)), split per region by [`splitAviationMap.py`](../../scripts/splitAviationMap.py) |
| **Consumer** | Enroute app: `GeoMaps::Waypoint` (compliance check), `GeoMaps::Airspace`, `FlightMap.qml` (styling and labels) |
| **Server path** | `{Continent}/{Region}.geojson`, plus a zopfli-compressed copy `{Region}.geojson.gz` |

Enroute Flight Navigation uses standard [GeoJSON](https://datatracker.ietf.org/doc/html/rfc7946) files to encode maps with aeronautical information. Every file is a single `FeatureCollection`. The files are serialized compactly and deterministically (`json.dumps(..., sort_keys=True, separators=(',', ':'))`).

## Map information

The `FeatureCollection` has an additional optional member called `info`. It is a semicolon-separated list of strings that describe the origin of the map data. The string may be empty even if the member exists. The current pipeline writes a single string of the form `Generated from openAIP and open flightmaps data, 2026-11-11`.

The deploy step ignores `info` when it decides whether a file has changed, so a new date alone does not trigger a re-upload.

## Properties common to all features

Every feature has these three properties:

- **TYP** gives the main type of the feature:
  - **AD**: airfields
  - **AS**: airspaces
  - **NAV**: navaids
  - **PRC**: procedures, which means traffic circuits, holding patterns in control zones, and arrival or departure routes for control zones
  - **WP**: waypoints, including (mandatory) reporting points and generic user-defined waypoints

  All features of the same **TYP** have the same geometry and the same list of optional and required properties. Each **TYP** is subdivided into categories, as described below.
- **CAT** is a string that gives the category of the feature, for example **AD-GLD** (glider site) or **CTR** (control zone). The possible values are listed below for every **TYP**.
- **NAM** is the name of the feature, as a human-readable string. It is optional only for procedures (TYP PRC).

---

## TYP AD: Airfields

Airfields are features whose geometry is always a `Point`. They have the properties listed below.

#### CAT (required)

The type of the airfield. It is exactly one of the following strings:

- **AD**: civil or civil/military airfield or airport, without information about runways
- **AD-GRASS**: civil or civil/military airfield or airport, without a paved runway
- **AD-PAVED**: civil or civil/military airfield or airport, with a paved runway
- **AD-INOP**: abandoned airfield
- **AD-GLD**: glider site
- **AD-MIL**: military airfield or airport, without information about runways
- **AD-MIL-GRASS**: military airfield, without a paved runway
- **AD-MIL-PAVED**: military airfield, with a paved runway
- **AD-UL**: ultralight flying site
- **AD-WATER**: sea airfield

#### COD (optional)

The ICAO code of the airfield, for example `"EDDE"`.

#### COM (optional)

Communication radio frequencies, separated by newline characters. Sort the entries as follows:

1. tower frequencies
2. ground frequencies
3. apron frequencies
4. other

Example: `"TWR 121.150 MHz\nGROUND 121.750 MHz\nAPRON 121.900 MHz"`.

#### ELE (required)

The elevation of the airfield, as a number in meters above mean sea level.

#### INF (optional)

Information radio frequencies (for example ATIS), separated by newline characters. Example: `"ATIS 133.450 MHz"`.

#### NAM (required)

The name of the airfield, for example `"ERFURT-WEIMAR"`.

#### NAV (optional)

Navigation frequencies of the airfield, such as ILS frequencies, separated by newline characters. The current pipeline does not produce this property.

#### ORI (optional)

The orientation of the most important runway, as a number between 0 and 360. Paved runways are more important than unpaved runways. Among runways of the same type, longer runways are more important.

#### OTH (optional)

Other frequencies of the airfield, separated by newline characters. Examples are frequencies that switch on the lights, or frequencies for nearby airspaces.

#### RWY (optional)

A description of all operational runways, separated by newline characters. Example: `"10/28, 2600x50m, ASPH, 095°"`.

#### TYP (required)

Always `"AD"`.

#### VAR (optional)

The magnetic variation, as a number in the range 0–360°.

---

## TYP AS: Airspaces

Airspaces are features whose geometry is always a `Polygon`. They have the properties listed below.

#### BOT (required)

The lower boundary of the airspace, as a string in one of the following forms:

- **GND**: ground level
- **5500**: 5500 ft above sea level
- **1000 AGL**: 1000 ft above ground level
- **FL 130**: flight level 130

Some airspaces have a lower boundary of the form "FL 115, but not below 3000 ft above ground". In that case **BOT** holds the primary limit (`"FL 115"`) and the optional property **BMN** holds the secondary one.

#### BMN (optional)

A minimum for the lower boundary, as a string in the form described under **BOT**. If present, the effective lower boundary is the higher of **BOT** and **BMN**.

Example: **BOT** = `"FL 115"` and **BMN** = `"3000 AGL"` means "FL 115, but at least 3000 ft above ground".

Apps that do not know this property may ignore it; the primary limit in **BOT** remains valid on its own.

#### CAT (required)

The category of the airspace. It is exactly one of the following strings:

- **A**: airspace class A
- **ATZ**: aerodrome traffic zone
- **B**: airspace class B
- **C**: airspace class C
- **CTR**: control zone
- **D**: airspace class D
- **DNG**: danger area, except parachute jumping exercise zones (for these, see **PJE**)
- **E**: airspace class E
- **F**: airspace class F
- **FIR**: flight information region
- **FIS**: flight information service sector
- **G**: airspace class G
- **GLD**: gliding sector
- **NRA**: nature reserve area
- **P**: prohibited area
- **PJE**: parachute jumping exercise zone
- **R**: restricted area
- **RMZ**: radio mandatory zone
- **SUA**: special use airspace
- **TIA**: terminal information area
- **TIZ**: terminal information zone
- **TMZ**: transponder mandatory zone

#### ID (optional)

A free-text identifier of the airspace in its source database. It is currently set only for airspaces from open flightmaps, where it holds the OFMX `mid`.

#### MLI, MLM (optional)

Ready-made map labels for the airspace. The app shows **MLI** when the user prefers imperial altitude units and **MLM** when the user prefers metric units. Each label is a `" • "`-separated list of parts, such as the airspace class or name, followed by the vertical limits. A secondary limit is appended with a slash. Example: `"D • FL 115/3000 AGL - FL 175"`.

#### NAM (required)

The name of the airspace, as free text.

#### SBO (required)

The lower boundary of the airspace in feet, as a number. It assumes that GND = 0 ft and the ICAO standard atmosphere. The app uses this value to decide which airspaces to show or hide when the user sets an airspace altitude limit.

> **Note:** Nature reserve areas (`CAT` = `NRA`) from open flightmaps currently do not carry **SBO**. The app treats a missing value as 0.

#### TMX (optional)

A maximum for the upper boundary, as a string in the form described under **BOT**. If present, the effective upper boundary is the lower of **TOP** and **TMX**.

Example: **TOP** = `"1000 AGL"` and **TMX** = `"1650"` means "1000 ft above ground, but at most 1650 ft above sea level".

Apps that do not know this property may ignore it; the primary limit in **TOP** remains valid on its own.

#### TOP (required)

The upper boundary of the airspace, as a string in the form described under **BOT**.

#### TYP (required)

Always `"AS"`.

---

## TYP NAV: Navaids

Navaids are features whose geometry is always a `Point`. They have the properties listed below.

#### CAT (required)

The category of the navaid. It is one of the following strings:

- **DME**
- **NDB**
- **VOR**
- **VOR-DME**
- **VORTAC**
- **DVOR**
- **DVOR-DME**
- **DVORTAC**

#### COD (required)

The code name of the navaid, for example `"KRH"`.

#### ELE (optional)

The elevation of the navaid, in meters above sea level.

#### MOR (required)

The Morse code of the station's identifier.

#### NAM (required)

The full-text name of the navaid, for example `"Karlsruhe"`.

#### NAV (required)

The radio frequency of the navaid, as a string of the form `"341.0 kHz"`, `"113.60 MHz"` or `"113.60 MHz • 83X"`.

#### TYP (required)

Always `"NAV"`.

#### VAR (optional)

The magnetic variation, as a number in the range 0–360°.

---

## TYP PRC: Procedures

Procedures are traffic circuits, holding patterns, and arrival, departure and transit routes. Their geometry is always a `LineString`. They have the properties listed below.

#### CAT (required)

Always `"PRC"`.

#### GAC (optional)

A guess at whether the procedure is meant for standard aircraft (`"blue"`) or for gliders, ultralights and helicopters (`"red"`).

#### NAM (optional)

The name of the procedure, for example `"TFC Glider"`.

#### TYP (required)

Always `"PRC"`.

#### USE (required)

The type of the procedure. It is one of the following strings:

- **ARR**: arrival route
- **DEP**: departure route
- **HLD**: holding pattern
- **TFC**: traffic circuit
- **TRA**: transit route

---

## TYP WP: Waypoints

Waypoints are features whose geometry is always a `Point`. They have the properties listed below.

#### CAT (required)

The category of the waypoint. It is one of the following strings:

- **MRP**: mandatory reporting point
- **NOTAM**: location of a NOTAM
- **RP**: reporting point
- **WP**: generic waypoint

#### COD (required if CAT is MRP or RP)

A code name of the waypoint, for example `"EDDE-S1"`. The app uses this property for the ID field in the waypoint description dialog.

#### COM (optional)

An associated frequency, for example `"EDDE - TWR 121.150 MHz"`.

#### ELE (optional)

The elevation of the waypoint, in meters above sea level.

#### ICA (optional)

The ICAO code of an associated airfield, for example `"EDDE"`.

#### MID (optional)

The internal ID of the waypoint in the source database, for example `"7295"`.

#### NAM (required)

The name of the waypoint, for example `"ERFURT-WEIMAR (SIERRA1)"`. The app uses this property as the title of the waypoint description dialog.

#### NOT (optional)

Notes attached to the waypoint.

#### SCO (required if CAT is MRP or RP)

A short designator of the waypoint, for example `"S1"`. The app uses this property as the display name of the point on the moving map.

#### TYP (required)

Always `"WP"`.

#### VAR (optional)

The magnetic variation, as a number in the range 0–360°.

---

## Changes to this specification

- **2026-11**: moved here from the GitHub wiki. Aligned with the files that are actually produced and consumed:
  - added the airspace category **RMZ**, the airspace label properties **MLI**/**MLM**, and the navaid category **DME**
  - airspace **ID** is now optional
  - documented that **SBO** is missing for NRA
  - fixed copy-and-paste errors in the PRC/WP sections
  - removed a wrong example for AD **NAV** (the pipeline does not produce that property)

The history before the move is in the [wiki history](https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation/_history).
