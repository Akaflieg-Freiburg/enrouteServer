#!/usr/bin/python3

import os

"""
METAR Station DB
====================================
Toolset to create a list of METAR stations known to the aviation weather center.

This script reads the list of known METAR stations from the aviation weather
center and writes a plain text file in ISO-8859-1 encoding ("Latin1"). The first
line is a short description of the content. Afterwards, starting from byte #xxx,
there are about 10,000 entries, each of which is exactly 5 characters long. The
entries are sorted in alphabetical order. The file is written to the "out"
directory. If the directory does not exist, it is created.
"""

from datetime import date
import gzip
import json
import requests


#
# Main function: run the methods of this module on test data
#
os.makedirs('out', exist_ok=True)

try:
    response = requests.get('https://aviationweather.gov/data/cache/stations.cache.json.gz')
    response.raise_for_status()
    # Code here will only run if the request is successful
except requests.exceptions.HTTPError as errh:
    print(errh)
    exit(-1)
except requests.exceptions.ConnectionError as errc:
    print(errc)
    exit(-1)
except requests.exceptions.Timeout as errt:
    print(errt)
    exit(-1)
except requests.exceptions.RequestException as err:
    print(err)
    exit(-1)
decompressed_data = gzip.decompress(response.content)
stations = json.loads(decompressed_data)
res = []
for station in stations:
    if 5 < len(station['icaoId']):
        continue
    res.append(station['icaoId'].ljust(5))
res.sort()

outfile = open("out/METAR Stations.txt", 'w', encoding='ISO-8859-1')
outfile.write("METAR Station Database. Compiled from data provided by the Aviation Weather Center on " + date.today().strftime("%d/%m/%Y") + "\n")
outfile.write("".join(res))
