import requests
import os
import shutil
from datetime import datetime
import email.utils
from urllib.parse import urlparse
import paramiko
import TripKit2VACCollection

collections = [
    {
        'attribution': 'Service de l’Information Aéronautique (SIA)',
        'description': 'Visual approach charts for France',
        'continent': 'Europe',
        'name': 'France',
        'url': 'sftp://www595.your-server.de/France VAC.zip',
        'sftp_user': 'akafli_0'
    }
]

# Fetch the password securely from the system's environment variables
SFTP_PASSWORD = os.environ.get('SFTP_PASSWORD')

for collection in collections:
    print(f"\nProcessing: {collection['name']}")
    local_filename_zip = 'tripkit_storage/' + collection['name'] + '.zip'
    local_filename_vac = collection['name'] + '.vac'

    parsed_url = urlparse(collection['url'])
    scheme = parsed_url.scheme.lower()

    remote_time = None
    do_download = False

    # ---------------------------------------------------------
    # SCENARIO A: HTTP / HTTPS
    # ---------------------------------------------------------
    if scheme in ['http', 'https']:
        try:
            response = requests.head(collection['url'])
            response.raise_for_status()

            remote_time_str = response.headers.get('Last-Modified')
            if not remote_time_str:
                print("Server didn't provide Last-Modified header. Skipping.")
                continue

            remote_time = datetime(*email.utils.parsedate(remote_time_str)[:6])

            # Check local file time
            if os.path.exists(local_filename_zip):
                local_time = datetime.fromtimestamp(os.path.getmtime(local_filename_zip))
                do_download = remote_time > local_time
                print(f"Remote file: {remote_time}, Local file: {local_time}")
            else:
                do_download = True

            if do_download:
                print("Downloading via HTTP/HTTPS...")
                os.makedirs(os.path.dirname(local_filename_zip), exist_ok=True)
                response = requests.get(collection['url'], stream=True)
                response.raise_for_status()
                with open(local_filename_zip, 'wb') as file:
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
            ssh.connect(hostname=host, port=port, username=collection.get('sftp_user'), password=SFTP_PASSWORD)
            sftp = ssh.open_sftp()

            # Get remote file stats for the timestamp
            file_stat = sftp.stat(filepath)
            remote_time = datetime.fromtimestamp(file_stat.st_mtime)

            # Check local file time
            if os.path.exists(local_filename_zip):
                local_time = datetime.fromtimestamp(os.path.getmtime(local_filename_zip))
                do_download = remote_time > local_time
                print(f"Remote file: {remote_time}, Local file: {local_time}")
            else:
                do_download = True

            if do_download:
                print("Downloading via SFTP...")
                os.makedirs(os.path.dirname(local_filename_zip), exist_ok=True)
                # SFTP handles the chunking and streaming internally via the get() method
                sftp.get(filepath, local_filename_zip)
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

    print("Converting TripKit to VAC collection...")
    TripKit2VACCollection.tripKit2VACCollection(
        local_filename_zip,
        local_filename_vac,
        name=collection['name'],
        description=collection.get('description'),
        attribution=collection.get('attribution'),
        publicationDate=remote_time.strftime('%Y%m%d'))

    out_dir = "out/" + collection['continent'] + "/"
    os.makedirs(out_dir, exist_ok=True) # Ensure the output directory exists before moving
    shutil.move(local_filename_vac, out_dir + local_filename_vac)
    print("Processing complete.\n")
