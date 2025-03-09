import requests
import os
import shutil
from datetime import datetime
import email.utils  # For parsing HTTP date strings
import GeoTIFF2MBTILES

maps = [
    {
        'attribution': 'Federal Office of Topography swisstopo',
        'description': 'Swiss ICAO Chart. For information only. The <a href="https://www.geo.admin.ch/en/general-terms-of-use-fsdi">license conditions</a> do not allow operational use.',
        'continent': 'Europe',
        'name': 'Switzerland ICAO Chart',
        'url': 'https://data.geo.admin.ch/ch.bazl.luftfahrtkarten-icao/luftfahrtkarten-icao/luftfahrtkarten-icao_total_50_2056.tif'
    },
    {
        'attribution': 'Federal Office of Topography swisstopo',
        'description': 'Swiss Glider Chart. For information only. The <a href="https://www.geo.admin.ch/en/general-terms-of-use-fsdi">license conditions</a> do not allow operational use.',
        'continent': 'Europe',
        'name': 'Switzerland Glider Chart',
        'url': 'https://data.geo.admin.ch/ch.bazl.segelflugkarte/segelflugkarte/segelflugkarte_total_30_2056.tif'
    }
]

for map in maps:
    print(map['name'])
    chunk_size = 8192  # Download 8KB at a time (adjust as needed)
    local_filename_tiff = 'tiff_storage/' + map['name'] + '.tiff'
    local_filename_raster = map['name'] + '.raster'

    # Get the remote file's last modified time (from headers)
    response = requests.head(map['url'])  # HEAD request to avoid downloading the file
    response.raise_for_status()

    # Check if 'Last-Modified' header exists
    remote_time_str = response.headers.get('Last-Modified')
    if not remote_time_str:
        print("Server didn't provide Last-Modified header. Downloading anyway.")
        do_download = True
    else:
        # Parse the remote timestamp (e.g., "Fri, 07 Mar 2025 12:00:00 GMT")
        remote_time = datetime(*email.utils.parsedate(remote_time_str)[:6])

    # Get local file's last modified time (if it exists)
    if os.path.exists(local_filename_tiff):
        local_time = datetime.fromtimestamp(os.path.getmtime(local_filename_tiff))
        do_download = remote_time > local_time
        print(f"Remote file: {remote_time}, Local file: {local_time}")
    else:
        do_download = True  # No local file, so download
    
    if not do_download:
        print("No download")
        continue

    # Stream the download
    response = requests.get(map['url'], stream=True)
    response.raise_for_status()  # Check for errors

    # Save the file in chunks
    directory = os.path.dirname(local_filename_tiff)
    os.makedirs(directory, exist_ok=True)
    with open(local_filename_tiff, 'wb') as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:  # Filter out keep-alive chunks
                file.write(chunk)
    print("Download complete!")
    directory = os.path.dirname(local_filename_raster)
    if directory != "":
        os.makedirs(directory, exist_ok=True)
    GeoTIFF2MBTILES.GeoTIFF2MBTILES(local_filename_tiff, local_filename_raster)
    GeoTIFF2MBTILES.update_mbtiles_metadata(local_filename_raster, map['attribution'], map['description'])
    shutil.move(local_filename_raster, "staging/" + map['continent'] + "/" + local_filename_raster)
