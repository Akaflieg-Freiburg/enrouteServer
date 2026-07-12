"""
TripKit2VACCollection
=====================

Convert a TripKit zip archive of georeferenced visual approach charts into an
SQLite VAC collection container, as consumed by Enroute Flight Navigation.

Container schema (schemaVersion 1)::

    CREATE TABLE metadata (key TEXT UNIQUE NOT NULL, value TEXT);
    -- required: ('schemaVersion','1'), ('name', ...)
    -- optional: ('description', ...), ('attribution', ...),
    --           ('publicationDate', 'yyyyMMdd')
    CREATE TABLE charts (
      name TEXT PRIMARY KEY,
      topLeftLat REAL NOT NULL,    topLeftLon REAL NOT NULL,
      topRightLat REAL NOT NULL,   topRightLon REAL NOT NULL,
      bottomLeftLat REAL NOT NULL, bottomLeftLon REAL NOT NULL,
      bottomRightLat REAL NOT NULL,bottomRightLon REAL NOT NULL,
      image BLOB NOT NULL          -- webp-encoded raster
    );

All coordinates are WGS84 degrees. Chart images are re-encoded to webp here on
the server, so the app never has to re-encode on the device.
"""

import io
import json
import os
import sqlite3
import zipfile

from PIL import Image

# Quality used when re-encoding chart images that are not already webp
WEBP_QUALITY = 90


def _isValid(lat, lon):
    if lat is None or lon is None:
        return False
    return (-90.0 <= lat <= 90.0) and (-180.0 <= lon <= 180.0)


def _corner(geoCorners, key):
    corner = geoCorners.get(key, {})
    return (corner.get('latitude'), corner.get('longitude'))


def _readTripKitTOC(zip):
    """Read chart entries from the TripKit files 'toc.json' and
    'charts/charts_toc.json'.

    :param zip: Open zipfile.ZipFile instance

    :returns: List of chart entry dictionaries with keys 'name', 'path' and
        'corners' (topLeft/topRight/bottomLeft/bottomRight as (lat, lon)
        tuples), or None if the archive is not a TripKit with a table of
        contents.
    """

    # TripKits usually keep their content in a top-level directory; find the
    # prefix by locating toc.json.
    prefix = None
    for fileName in zip.namelist():
        if fileName == 'toc.json' or fileName.endswith('/toc.json'):
            prefix = fileName[:-len('toc.json')]
            break
    if prefix is None:
        return None

    try:
        chartsTOC = json.loads(zip.read(prefix + 'charts/charts_toc.json'))
    except (KeyError, json.JSONDecodeError):
        return None

    entries = []
    for chart in chartsTOC.get('charts', []):
        name = chart.get('name')
        filePath = chart.get('filePath')
        if not name or not filePath:
            print("Skipping chart entry without name or filePath")
            continue

        geoCorners = chart.get('geoCorners', {})
        corners = {
            'topLeft': _corner(geoCorners, 'upperLeft'),
            'topRight': _corner(geoCorners, 'upperRight'),
            'bottomLeft': _corner(geoCorners, 'lowerLeft'),
            'bottomRight': _corner(geoCorners, 'lowerRight')
        }
        if not all(_isValid(lat, lon) for (lat, lon) in corners.values()):
            print(f"Skipping chart '{name}', which has invalid coordinates")
            continue

        # Some TripKits list file paths that do not exist in the archive; like
        # the app, fall back to the conventional 'charts/<name>-geo.<ext>'.
        path = prefix + filePath
        if path not in zip.namelist():
            ending = filePath.rpartition('.')[2]
            path = prefix + 'charts/' + name + '-geo.' + ending

        entries.append({'name': name, 'path': path, 'corners': corners})
    return entries


def _readVACFileNames(zip):
    """Read chart entries from zip archives without a table of contents, where
    coordinates are encoded in the image file names, in the form
    'name-geo_<left>_<top>_<right>_<bottom>.<ext>'.

    :param zip: Open zipfile.ZipFile instance

    :returns: List of chart entry dictionaries, as in _readTripKitTOC()
    """

    entries = []
    for path in zip.namelist():
        baseName = os.path.basename(path)
        stem, _, ending = baseName.rpartition('.')
        if not stem or ending.lower() not in ['webp', 'png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp', 'gif']:
            continue

        parts = stem.split('_')
        if len(parts) < 5:
            continue
        try:
            left, top, right, bottom = (float(x) for x in parts[-4:])
        except ValueError:
            continue
        if not (_isValid(top, left) and _isValid(bottom, right)):
            continue

        name = '_'.join(parts[:-4])
        if name.endswith('-geo'):
            name = name[:-len('-geo')]
        entries.append({
            'name': name,
            'path': path,
            'corners': {
                'topLeft': (top, left),
                'topRight': (top, right),
                'bottomLeft': (bottom, left),
                'bottomRight': (bottom, right)
            }
        })
    return entries


def _toWebp(imageData):
    """Return webp-encoded image data. Data that is already webp passes
    through unchanged; everything else is re-encoded via Pillow.

    :param imageData: Raw image data bytes

    :returns: webp-encoded image data bytes
    """

    if imageData[:4] == b'RIFF' and imageData[8:12] == b'WEBP':
        return imageData

    image = Image.open(io.BytesIO(imageData))
    if image.mode in ['RGBA', 'LA', 'PA'] or (image.mode == 'P' and 'transparency' in image.info):
        image = image.convert('RGBA')
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    buffer = io.BytesIO()
    image.save(buffer, 'WEBP', quality=WEBP_QUALITY, method=6)
    return buffer.getvalue()


def tripKit2VACCollection(zipFileName, vacFileName, name, description=None, attribution=None, publicationDate=None):
    """Convert a TripKit zip archive into an SQLite VAC collection container.

    Reads the charts listed in the TripKit's table of contents (or, for plain
    zip archives without one, charts whose coordinates are encoded in the file
    names), re-encodes the images to webp where necessary and writes the
    container file. The container is VACUUMed, so re-running with identical
    input produces identical output.

    :param zipFileName: Name of the input TripKit zip file

    :param vacFileName: Name of the SQLite container file that is written;
        pre-existing files are overwritten

    :param name: Collection name, stored in the metadata table (e.g. 'France')

    :param description: Optional description string for the metadata table

    :param attribution: Optional attribution string for the metadata table

    :param publicationDate: Optional publication date for the metadata table,
        in the form 'yyyyMMdd'

    :raises Exception: If the archive contains no usable charts or an image
        cannot be read
    """

    with zipfile.ZipFile(zipFileName) as zip:
        entries = _readTripKitTOC(zip)
        if not entries:
            entries = _readVACFileNames(zip)
        if not entries:
            raise Exception(f"The zip archive {zipFileName} does not contain any usable charts")

        if os.path.exists(vacFileName):
            os.remove(vacFileName)
        connection = sqlite3.connect(vacFileName)
        connection.execute("CREATE TABLE metadata (key TEXT UNIQUE NOT NULL, value TEXT)")
        connection.execute(
            "CREATE TABLE charts ("
            "name TEXT PRIMARY KEY, "
            "topLeftLat REAL NOT NULL, topLeftLon REAL NOT NULL, "
            "topRightLat REAL NOT NULL, topRightLon REAL NOT NULL, "
            "bottomLeftLat REAL NOT NULL, bottomLeftLon REAL NOT NULL, "
            "bottomRightLat REAL NOT NULL, bottomRightLon REAL NOT NULL, "
            "image BLOB NOT NULL)")

        metadata = [('schemaVersion', '1'), ('name', name)]
        if description:
            metadata.append(('description', description))
        if attribution:
            metadata.append(('attribution', attribution))
        if publicationDate:
            metadata.append(('publicationDate', publicationDate))
        connection.executemany("INSERT INTO metadata VALUES (?,?)", metadata)

        seenNames = set()
        numCharts = 0
        for entry in sorted(entries, key=lambda e: e['name']):
            if entry['name'] in seenNames:
                print(f"Skipping chart '{entry['name']}', which appears more than once")
                continue

            try:
                imageData = zip.read(entry['path'])
            except KeyError:
                print(f"Skipping chart '{entry['name']}', image file '{entry['path']}' is missing")
                continue
            imageData = _toWebp(imageData)

            corners = entry['corners']
            connection.execute(
                "INSERT INTO charts VALUES (?,?,?,?,?,?,?,?,?,?)",
                (entry['name'],
                 corners['topLeft'][0], corners['topLeft'][1],
                 corners['topRight'][0], corners['topRight'][1],
                 corners['bottomLeft'][0], corners['bottomLeft'][1],
                 corners['bottomRight'][0], corners['bottomRight'][1],
                 sqlite3.Binary(imageData)))
            seenNames.add(entry['name'])
            numCharts += 1

        if numCharts == 0:
            connection.close()
            os.remove(vacFileName)
            raise Exception(f"No chart from {zipFileName} could be converted")

        connection.commit()
        connection.execute("VACUUM")
        connection.close()
        print(f"Wrote {numCharts} charts to {vacFileName}")
