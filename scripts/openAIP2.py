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

def interpretLimit(limit, item):
    if limit['unit'] == 0:
        return 'FL ' + limit['value']
    value = 0
    if limit['unit'] == 1:
        value = round(limit['value']*3.2808)
    if limit['unit'] == 6:
        value = limit['value']
    if limit['referenceDatum'] == 0:
        if value == 0:
            return 'GND'
        return value + ' AGL'
    if limit['referenceDatum'] == 1:
        return value
    print('Invalid airspace limit')
    print(item)
    print(limit)
    exit(-1)

def readOpenAIPData(typeName, country):
    """Read data from the openAIP2 API.

    :param typeName: Name data ("navaids")

    :param country: two-letter country code, such as 'DE' or 'de'

    :returns: dictionary with data

    """

    my_headers = {'x-openaip-client-id' : os.environ['openAIP']}
    try:
        response = requests.get("https://api.core.openaip.net/api/"+typeName, headers=my_headers, params={'country': country.upper(), 'limit': 10000} )
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


def readOpenAIPAirspaces(country):
    """Read airspaces from the openAIP2 API.

    :param country: Country code, such as 'DE'

    :returns: GeoJSON feature array, in the format described here:
    https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    parsedResponse = readOpenAIPData('airspaces', country)
    features = []
    for item in parsedResponse['items']:
        properties = {}

        #
        # Look at the various types of airspace
        #
        # 0: Other
        if item['type'] == 1: # Restricted
            properties['CAT'] = 'R'
        if item['type'] == 2: # Danger
            if 'PARA' in item['name']:
                properties['CAT'] = 'PJE'
            else:
                properties['CAT'] = 'DNG'
        if item['type'] == 3: # Prohibited
            properties['CAT'] = 'P'
        if item['type'] == 4: # Controlled Tower Region (CTR)
            properties['CAT'] = 'CTR'
        if item['type'] == 5: # Transponder Mandatory Zone (TMZ)
            properties['CAT'] = 'TMZ'
        if item['type'] == 6: # Radio Mandatory Zone (RMZ)
            properties['CAT'] = 'RMZ'
        # 7: Terminal Maneuvering Area (TMA)
        # 8: Temporary Reserved Area (TRA)
        # 9: Temporary Segregated Area (TSA)
        # 10: Flight Information Region (FIR)
        # 11: Upper Flight Information Region (UIR)
        # 12: Air Defense Identification Zone (ADIZ)
        # 13: Airport Traffic Zone (ATZ)
        # 14: Military Airport Traffic Zone (MATZ)
        # 15: Airway
        # 16: Military Training Route (MTR)
        # 17: Alert Area
        # 18: Warning Area
        # 19: Protected Area
        # 20: Helicopter Traffic Zone (HTZ)
        if item['type'] == 21: # Gliding Sector
            properties['CAT'] = 'GLD'
        # 22: Transponder Setting (TRP)
        # 23: Traffic Information Zone (TIZ)
        # 24: Traffic Information Area (TIA)
        # 25: Military Training Area (MTA)

        #
        # If CAT has not yet been assigned, look at the ICAO class of the airspaceq
        # 
        if not 'CAT' in properties:
            if item['icaoClass'] == 0: # A
                properties['CAT'] = 'A'
            if item['icaoClass'] == 1: # B
                properties['CAT'] = 'B'
            if item['icaoClass'] == 2: # C
                properties['CAT'] = 'C'
            if item['icaoClass'] == 3: # D
                properties['CAT'] = 'C'

        #
        # If CAT has still not yet been assigned, ignore this airspace
        # 
        if not 'CAT' in properties:
            continue

        # Get properties
        #properties = {}
        #properties['BOT'] = interpretAltitudeLimit(airspace.find('ALTLIMIT_BOTTOM'))
        #if airspace.get('CATEGORY') == 'DANGER':
        #    if airspace.find('NAME').text.startswith('PARA'):
        #        properties['CAT'] = 'PJE'
        #    else:
        #        properties['CAT'] = 'DNG'
        #elif (airspace.get('CATEGORY') == 'GLIDING') or (airspace.get('CATEGORY') == 'WAVE'):
        #    properties['CAT'] = 'GLD'
        #elif airspace.get('CATEGORY') == 'PROHIBITED':
        #    properties['CAT'] = 'P'
        #elif airspace.get('CATEGORY') == 'RESTRICTED':
        #    properties['CAT'] = 'R'
        #else:
        #    properties['CAT'] = airspace.get('CATEGORY')
        properties['NAM'] = item['name']
        properties['TYP'] = "AS"
        properties['BOT'] = interpretLimit(item['lowerLimit'], item)
        properties['TOP'] = interpretLimit(item['upperLimit'], item)
        
        #
        # Generate feature
        #
        feature = {'type': 'Feature'}
        feature['geometry'] = item['geometry']
        feature['properties'] = properties
        features.append(feature)
    return features



def readOpenAIPNavaids(country):
    """Read navaids from the openAIP2 API.

    :param country: Country code, such as 'DE'

    :returns: GeoJSON feature array, in the format described here:
    https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    parsedResponse = readOpenAIPData('navaids', country)
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

#print(readOpenAIPAirspaces('DE'))
