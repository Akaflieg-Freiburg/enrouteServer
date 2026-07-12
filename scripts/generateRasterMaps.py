import requests
import os
import shutil
from datetime import datetime
import email.utils
from urllib.parse import urlparse
import paramiko
import GeoTIFF2MBTILES

maps = [
    {
        'attribution': 'Service de l’Information Aéronautique (SIA)',
        'description': 'France ICAO SIA 500k Map',
        'continent': 'Europe',
        'name': 'France ICAO Chart',
        'url': 'sftp://www595.your-server.de/France ICAO Chart.tiff', 
        'sftp_user': 'akafli_0' # Added user mapping here
    },
    {
        'attribution': 'Federal Office of Topography swisstopo',
        'description': 'Swiss ICAO Chart. For information only.',
        'continent': 'Europe',
        'name': 'Switzerland ICAO Chart',
        'url': 'https://data.geo.admin.ch/ch.bazl.luftfahrtkarten-icao/luftfahrtkarten-icao/luftfahrtkarten-icao_total_50_2056.tif'
    },
    {
        'attribution': 'Federal Office of Topography swisstopo',
        'description': 'Swiss Glider Chart. For information only. The <a href="https://www.geo.admin.ch/en/general-terms-of-use-fsdi">license conditions</a> do not allow operational use.',
        'continent': 'Europe',
        'name': 'Switzerland Glider Chart',
        'url': 'https://data.geo.admin.ch/ch.bazl.segelflugkarte/segelflugkarte/segelflugkarte_total_35_2056.tif'
    }

]

# Fetch the password securely from the system's environment variables
SFTP_PASSWORD = os.environ.get('SFTP_PASSWORD')

for map_data in maps:
    print(f"\nProcessing: {map_data['name']}")
    local_filename_tiff = 'tiff_storage/' + map_data['name'] + '.tiff'
    local_filename_raster = map_data['name'] + '.raster'

    parsed_url = urlparse(map_data['url'])
    scheme = parsed_url.scheme.lower()
    
    remote_time = None
    do_download = False

    # ---------------------------------------------------------
    # SCENARIO A: HTTP / HTTPS
    # ---------------------------------------------------------
    if scheme in ['http', 'https']:
        try:
            response = requests.head(map_data['url'])
            response.raise_for_status()
            
            remote_time_str = response.headers.get('Last-Modified')
            if not remote_time_str:
                print("Server didn't provide Last-Modified header. Skipping.")
                continue
                
            remote_time = datetime(*email.utils.parsedate(remote_time_str)[:6])
            
            # Check local file time
            if os.path.exists(local_filename_tiff):
                local_time = datetime.fromtimestamp(os.path.getmtime(local_filename_tiff))
                do_download = remote_time > local_time
                print(f"Remote file: {remote_time}, Local file: {local_time}")
            else:
                do_download = True

            if do_download:
                print("Downloading via HTTP/HTTPS...")
                os.makedirs(os.path.dirname(local_filename_tiff), exist_ok=True)
                response = requests.get(map_data['url'], stream=True)
                response.raise_for_status()
                with open(local_filename_tiff, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                print("Download complete!")

        except Exception as e:
            print(f"HTTP Error occurred: {e}")
            continue

    # ---------------------------------------------------------
    # SCENARIO B: SFTP
    # ---------------------------------------------------------
    elif scheme == 'sftp':
        if not SFTP_PASSWORD:
            print("SFTP_PASSWORD environment variable not set. Skipping SFTP download.")
            continue
            
        host = parsed_url.hostname
        port = parsed_url.port or 22
        filepath = parsed_url.path
        
        # We start the name with a slash, but some servers prefer relative paths. 
        # If it fails, you might need to strip the leading slash: filepath = filepath.lstrip('/')
        
        try:
            # Set up SSH and SFTP clients
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, port=port, username=map_data.get('sftp_user'), password=SFTP_PASSWORD)
            sftp = ssh.open_sftp()
            
            # Get remote file stats for the timestamp
            file_stat = sftp.stat(filepath)
            remote_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            # Check local file time
            if os.path.exists(local_filename_tiff):
                local_time = datetime.fromtimestamp(os.path.getmtime(local_filename_tiff))
                do_download = remote_time > local_time
                print(f"Remote file: {remote_time}, Local file: {local_time}")
            else:
                do_download = True
                
            if do_download:
                print("Downloading via SFTP...")
                os.makedirs(os.path.dirname(local_filename_tiff), exist_ok=True)
                # SFTP handles the chunking and streaming internally via the get() method
                sftp.get(filepath, local_filename_tiff)
                print("Download complete!")
                
            # Always close connections when done
            sftp.close()
            ssh.close()
            
        except Exception as e:
            print(f"SFTP Error occurred: {e}")
            continue
            
    else:
        print(f"Unsupported protocol: {scheme}")
        continue

    # ---------------------------------------------------------
    # PROCESSING (Common for both)
    # ---------------------------------------------------------
    if not do_download:
        print("No download needed.")
        continue
        
    print("Processing raster maps...")
    directory = os.path.dirname(local_filename_raster)
    if directory != "":
        os.makedirs(directory, exist_ok=True)
        
    GeoTIFF2MBTILES.GeoTIFF2MBTILES(local_filename_tiff, local_filename_raster)
    GeoTIFF2MBTILES.update_mbtiles_metadata(local_filename_raster, map_data['attribution'], map_data['description'], remote_time)
    
    out_dir = "out/" + map_data['continent'] + "/"
    os.makedirs(out_dir, exist_ok=True) # Ensure the output directory exists before moving
    shutil.move(local_filename_raster, out_dir + local_filename_raster)
    print("Processing complete.\n")