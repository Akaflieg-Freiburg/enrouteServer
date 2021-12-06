#!/bin/python

"""
opeenAIP2
=======================================================================================================
Toolset to read aviation data from the openAIP2 web site and to transform the
data into the GeoJSON format described here:
https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation
"""

import json
import requests
import os

# Dictionary representing the morse code chart
MORSE_CODE_DICT = { 'A':'•‒', 'B':'‒•••',
                    'C':'‒•‒•', 'D':'‒••', 'E':'•',
                    'F':'••‒•', 'G':'‒‒•', 'H':'••••',
                    'I':'••', 'J':'•‒‒‒', 'K':'‒•‒',
                    'L':'•‒••', 'M':'‒‒', 'N':'‒•',
                    'O':'‒‒‒', 'P':'•‒‒•', 'Q':'‒‒•‒',
                    'R':'•‒•', 'S':'•••', 'T':'‒',
                    'U':'••‒', 'V':'•••‒', 'W':'•‒‒',
                    'X':'‒••‒', 'Y':'‒•‒‒', 'Z':'‒‒••',
                    '1':'•‒‒‒‒', '2':'••‒‒‒', '3':'•••‒‒',
                    '4':'••••‒', '5':'•••••', '6':'‒••••',
                    '7':'‒‒•••', '8':'‒‒‒••', '9':'‒‒‒‒•',
                    '0':'‒‒‒‒‒', ', ':'‒‒••‒‒', '•':'•‒•‒•‒',
                    '?':'••‒‒••', '/':'‒••‒•', '‒':'‒••••‒',
                    '(':'‒•‒‒•', ')':'‒•‒‒•‒'}


def morse(string):
    result = ""
    for letter in string.upper():
        if letter in MORSE_CODE_DICT:
            result = result + MORSE_CODE_DICT[letter] + " "
    return result

def readOpenAIPData(typeName):
    """Read data from the openAIP2 API.

    :param typeName: Name data ("navaids")

    :returns: dictionary with data

    """

    my_headers = {'x-openaip-client-id' : os.environ['openAIP']}
    try:
        response = requests.get("https://api.core.openaip.net/api/navaids", headers=my_headers, params={'country': 'DE', 'limit': 10000} )
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

    parsedResponse = response.json()
    if parsedResponse['totalPages'] > 1:
        print('Limit exceeded')
        exit(-1)
    return parsedResponse

def readOpenAIPNavaids():
    """Read navaids from the openAIP2 API.

    :returns: GeoJSON feature array, in the format described here:
    https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    parsedResponse = readOpenAIPData('navaids')
    features = []
    for item in parsedResponse['items']:
        #
        # Ignore the following navaids
        #
        if item['type'] == 0:   # DME
            continue
        if item['type'] == 1:   # TACAN
            continue

        #
        # Get properties
        #
        properties = {}

        if item['type'] == 2:
            properties['CAT'] = "NDB"
        if item['type'] == 3:
            properties['CAT'] = "VOR"
        if item['type'] == 4:
            properties['CAT'] = "VOR-DME"
        if item['type'] == 5:
            properties['CAT'] = "VORTAC"
        if item['type'] == 6:
            properties['CAT'] = "DVOR"
        if item['type'] == 7:
            properties['CAT'] = "DVOR-DME"
        if item['type'] == 8:
            properties['CAT'] = "DVORTAC"

        properties['COD'] = item['identifier']
        properties['ELE'] = item['elevation']['value']
        properties['NAM'] = item['name']

        freq = item['frequency']['value']
        if item['frequency']['unit'] == 1:
            freq += ' kHz'
        if item['frequency']['unit'] == 2:
            freq += ' MHz'
        if 'channel' in item:
            freq += " • " + item['channel']
        properties['NAV'] = freq

        properties['MOR'] = morse(item['identifier'])
        properties['TYP'] = 'NAV'

        #
        # Generate feature
        #
        feature = {'type': 'Feature'}
        feature['geometry'] = item['geometry']
        feature['properties'] = properties
        features.append(feature)
    return features

#
# Main program starts here
#

print(readOpenAIPNavaids())
