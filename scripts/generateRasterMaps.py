import requests
import os
from datetime import datetime
import email.utils  # For parsing HTTP date strings


maps = [
    {
        'attribution': 'Federal Office of Topography swisstopo',
        'description': 'Official Swiss ICAO Chart',
        'continent': 'Europe',
        'name': 'Switzerland ICAO Chart',
        'url': 'https://data.geo.admin.ch/ch.bazl.luftfahrtkarten-icao/luftfahrtkarten-icao/luftfahrtkarten-icao_total_50_2056.tif'
    },
    {
        'attribution': 'Federal Office of Topography swisstopo',
        'description': 'Official Swiss Glider Chart',
        'continent': 'Europe',
        'name': 'Switzerland Glider Chart',
        'url': 'https://data.geo.admin.ch/ch.bazl.segelflugkarte/segelflugkarte/segelflugkarte_total_30_2056.tif'
    }
]

for map in maps:
    print(map['attribution'])
    chunk_size = 8192  # Download 8KB at a time (adjust as needed)
    local_filename = map['name'] + '.tiff'

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
    if os.path.exists(local_filename):
        local_time = datetime.fromtimestamp(os.path.getmtime(local_filename))
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
    with open(local_filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:  # Filter out keep-alive chunks
                file.write(chunk)
    print("Download complete!")