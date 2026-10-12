import requests
import os
import shutil
import sys
from datetime import datetime
import email.utils
from urllib.parse import urlparse
import paramiko
import GeoTIFF2MBTILES
import OFMX
import SlippyTiles2MBTILES

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

#
# open flightmaps raster VFR charts. Each entry is (OFM region code, region name
# as in regions.py). The region name must match regions.py exactly, because
# deploy-hetzner.py looks up the bounding box by searching the file name for it.
# Only regions for which open flightmaps publishes tiles are listed.
#
ofm_maps = [
    ('lovv', 'Austria'),
    ('ebbu', 'Belgium'),
    ('lbsr', 'Bulgaria'),
    ('ldzo', 'Croatia'),
    ('lkaa', 'Czech Republic'),
    ('ekdk', 'Denmark'),
    ('efin', 'Finland'),
    ('lf',   'France'),
    ('ed',   'Germany'),
    ('lggg', 'Greece'),
    ('lhcc', 'Hungary'),
    ('li',   'Italy'),
    ('ehaa', 'Netherlands'),
    ('epww', 'Poland'),
    ('lrbb', 'Romania'),
    ('lzbb', 'Slovakia'),
    ('ljla', 'Slovenia'),
    ('esaa', 'Sweden'),
    ('lsas', 'Switzerland'),
]
OFM_CONTINENT = 'Europe'
OFM_URL = 'https://storage.googleapis.com/snapshots.openflightmaps.org/live/{airac}/tiles/{code}/noninteractive/epsg3857/slippyTiles_clipped.zip'
OFM_STORAGE = 'ofm_storage'   # ofm_storage/{airac}/{code}.zip, plus {code}.zip.etag sidecar
OFM_ATTRIBUTION = 'open flightmaps association (OFMA)'

# Fetch the password securely from the system's environment variables
SFTP_PASSWORD = os.environ.get('SFTP_PASSWORD')

# Optional command line arguments restrict the run to maps whose name contains
# one of the arguments, e.g. "python3 generateRasterMaps.py Slovenia".
name_filters = sys.argv[1:]

def is_selected(name):
    return (not name_filters) or any(f in name for f in name_filters)

for map_data in maps:
    if not is_selected(map_data['name']):
        continue
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


# ---------------------------------------------------------
# open flightmaps raster charts
# ---------------------------------------------------------
airac = OFMX.currentAirac()
cycle_dir = os.path.join(OFM_STORAGE, airac)
print(f"\nOFM: Current AIRAC cycle is {airac}")

def remove_old_ofm_cycles():
    """Delete cached zips of AIRAC cycles other than the current one"""
    if not os.path.isdir(OFM_STORAGE):
        return
    for entry in os.listdir(OFM_STORAGE):
        path = os.path.join(OFM_STORAGE, entry)
        if os.path.isdir(path) and (entry != airac):
            print(f"Removing cached OFM data for cycle {entry}")
            shutil.rmtree(path)

for code, region in ofm_maps:
    name = f"{region} VFR Chart (open flightmaps)"
    if not is_selected(name):
        continue
    print(f"\nProcessing: {name}")

    url = OFM_URL.format(airac=airac, code=code)
    local_filename_zip = os.path.join(cycle_dir, code + '.zip')
    local_filename_etag = local_filename_zip + '.etag'
    local_filename_raster = name + '.raster'

    remote_time = None
    do_download = False

    try:
        response = requests.head(url)
        if response.status_code == 404:
            print(f"OFM: no raster tiles for {code} in cycle {airac}, skipping")
            continue
        response.raise_for_status()

        remote_time_str = response.headers.get('Last-Modified')
        if not remote_time_str:
            print("Server didn't provide Last-Modified header. Skipping.")
            continue
        remote_time = datetime(*email.utils.parsedate(remote_time_str)[:6])
        remote_etag = response.headers.get('ETag', '')

        # Check local file time and ETag
        if os.path.exists(local_filename_zip):
            local_time = datetime.fromtimestamp(os.path.getmtime(local_filename_zip))
            local_etag = None
            if os.path.exists(local_filename_etag):
                with open(local_filename_etag) as file:
                    local_etag = file.read().strip()
            do_download = (remote_time > local_time) or (remote_etag != local_etag)
            print(f"Remote file: {remote_time}, Local file: {local_time}")
        else:
            do_download = True

        if do_download:
            print("Downloading via HTTP/HTTPS...")
            os.makedirs(cycle_dir, exist_ok=True)
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(local_filename_zip + '.part', 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        file.write(chunk)
            os.replace(local_filename_zip + '.part', local_filename_zip)
            with open(local_filename_etag, 'w') as file:
                file.write(remote_etag)
            timestamp = remote_time.timestamp()
            os.utime(local_filename_zip, (timestamp, timestamp))
            print("Download complete!")
            # The new cycle is evidently published, so older cycles are no
            # longer needed.
            remove_old_ofm_cycles()

    except Exception as e:
        print(f"HTTP Error occurred: {e}")
        continue

    if not do_download:
        print("No download needed.")
        continue

    print("Processing raster maps...")
    try:
        SlippyTiles2MBTILES.SlippyTiles2MBTILES(local_filename_zip, local_filename_raster, name)
    except Exception as e:
        print(f"Conversion error occurred: {e}")
        if os.path.exists(local_filename_raster):
            os.remove(local_filename_raster)
        continue
    description = f"{region} VFR chart by open flightmaps, AIRAC {airac}. For information only."
    GeoTIFF2MBTILES.update_mbtiles_metadata(local_filename_raster, OFM_ATTRIBUTION, description, remote_time)

    out_dir = "out/" + OFM_CONTINENT + "/"
    os.makedirs(out_dir, exist_ok=True)
    shutil.move(local_filename_raster, out_dir + local_filename_raster)
    print("Processing complete.\n")
