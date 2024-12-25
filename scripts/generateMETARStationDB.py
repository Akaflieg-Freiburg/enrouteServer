#!/usr/bin/python3

import os

"""
flarmDB
====================================
Toolset to create a compact database the maps Flarm IDs to aircraft callsigns.
"""

from datetime import date
import gzip
import json
import re
import requests


def A(dictionary):
    """Read a Flarmnet database in fln format (as also used by
    LXNavigation/XCSoar, WinPilot, LK8000, ClearNav).  Files of this form can be
    downloaded from Flarmnet, at this url:
    https://www.flarmnet.org/static/files/wfn/data.fln The method fills a
    dicitionary that maps Flarm IDs to aircraft callsigns. Input data where the
    'callsign' field is not obviously a well-defined callsign are ignored. This
    function will raise an exception on error

    :param inFileName: Name of input file

    :param dictionary: Dictionary to which the results will be appended

    :returns: String that describes the input file version

    """

    # Regular expression to check if a callsign is valid
    validReg = re.compile('^([A-Z0-9]{1,2}-[A-Z0-9]*|N[A-Z0-9]{2,6})$')

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
    response.encoding = 'utf-8'
    lines = response.text.splitlines()
    stations = json.loads(decompressed_data)
    for station in stations:
        print(station['icaoId'])
    return "Flarmnet Data version "+version




def readMETARStationDB(outFileName):
    """Read a Flarmnet and an OGN database and combines the data. The method
    writes a plain text file in ISO-8859-1 encoding ("Latin1"). The first line
    is a short description of the content. Every following line is exactly 24
    bytes long.

    - Bytes  0 -  5 of the line contain the Flarm ID
    - Bytes  7 - 22 of the line contain the aircraft callsign, left justified
      and filled with space

    The lines in the output file are sorted alphabetically by Flarm ID.

    This function will raise an exception on error

    :param flarmnetFileName: Name of input file

    :param ognFileName: Name of input file

    :param outFileName: Name of output file

    """

    result = {}

    flarmnetversion = A(result)
    version = "METAR Station Database. Compiled from \n"

    outfile = open(outFileName, 'w', encoding='ISO-8859-1')
    outfile.write(version)
    for FLARMID, callsign in sorted(result.items()):
        outfile.write(FLARMID)
        outfile.write(",")
        outfile.write(callsign.ljust(16))
        outfile.write("\n")


#
# Main function: run the methods of this module on test data
#
os.makedirs('out', exist_ok=True)
readMETARStationDB('out/METAR Stations.txt')
