# Flarm ID database (`Flarm Database.txt`)

*Audience: developers of Enroute Flight Navigation and the maintainer. This is the normative specification of the Flarm ID → registration database.*

| | |
|---|---|
| **Producer** | [`generateFlarmDB.py`](../../scripts/generateFlarmDB.py) (run by `generateAndDeployFLARMDB.sh`) |
| **Consumer** | Enroute app: `Traffic::FlarmnetDB` |
| **Server path** | `Flarm Database.txt` (top level, no continent directory), plus `Flarm Database.txt.gz` |

The app uses this database for one purpose only: to look up the official registration (`D-KLJC`) of an aircraft from its FLARM device ID (`DDDCDD`).

## Sources

The producer merges two public databases:

1. [Flarmnet](https://www.flarmnet.org) (`https://www.flarmnet.org/files/data.fln`)
2. the [Open Glider Network device database](http://ddb.glidernet.org) (`http://ddb.glidernet.org/download`)

If both sources contain the same ID, **Flarmnet wins**. Entries whose registration does not look like a real registration are dropped. A real registration matches `^([A-Z0-9]{1,2}-[A-Z0-9]*|N[A-Z0-9]{2,6})$`, for example `D-KLJC` or `N135GS`.

## File format

The file is plain text in ISO-8859-1 ("Latin-1") encoding.

```
FLARM ID database. Compiled from Flarmnet Data version 00db84 and Open Glider Network Data version 09-Sep-2026
000000,D-2188          
00001F,D-KHGA          
0000B1,D-9431          
000824,N6044           
```

- **Line 1** is a free-text comment of arbitrary length. The deploy step ignores this line when it decides whether the file has changed.
- **Every following line is exactly 24 bytes long:**
  - bytes 0–5: the FLARM device ID, six upper-case hexadecimal digits
  - byte 6: a comma
  - bytes 7–22: the registration, left-justified and padded with spaces to 16 bytes
  - byte 23: `\n`
- The lines are sorted alphabetically by device ID. The app relies on the sort order and on the fixed record length: it looks up an ID by binary search directly in the file. **Any line with a different length breaks the lookup.**

## Changes to this specification

- **2026-11**: moved here from the GitHub wiki. Documented the merge with Open Glider Network data, the actual header line, the byte layout and the METAR station file.
- **2026-11**: removed the section on `METAR Stations.txt`. The app never read that file, and it has been deleted from the server ([#75](https://github.com/Akaflieg-Freiburg/enrouteServer/issues/75)).
