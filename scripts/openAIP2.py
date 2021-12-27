#!/bin/python

"""
openAIP2
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
    if limit['unit'] == 6:
        return 'FL ' + str(limit['value'])
    value = 0
    if limit['unit'] == 0:
        value = str(round(limit['value']*3.2808))
    if limit['unit'] == 1:
        value = str(limit['value'])
    if limit['referenceDatum'] == 0:
        if value == "0":
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


def readOpenAIPAirports(country):
    """Read airspaces from the openAIP2 API.

    :param country: Country code, such as 'DE'

    :returns: GeoJSON feature array, in the format described here:
        https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    parsedResponse = readOpenAIPData('airports', country)

    with open('filename.txt', 'w') as f:
        print(parsedResponse, file=f)

    features = []
    for item in parsedResponse['items']:
        if item['name'] == 'REISELFINGEN':
            print(item)

        properties = {}

        #
        # Look at the various types of airport
        #

        
        if item['type'] == 0: # 0: Airport (civil/military)
            properties['CAT'] = 'AD'
        if item['type'] == 1: # 1: Glider Site
            properties['CAT'] = 'AD-GLD'
        if item['type'] == 2: # 2: Airfield Civil
            properties['CAT'] = 'AD'
        if item['type'] == 3: # 3: International Airport
            properties['CAT'] = 'AD'
        # 4: Heliport Military
        if item['type'] == 5: # 5: Military Aerodrome
            properties['CAT'] = 'AD-MIL'
        if item['type'] == 6: # 6: Ultra Light Flying Site
            properties['CAT'] = 'AD-UL'
        # 7: Heliport Civil
        if item['type'] == 8: # 8: Aerodrome Closed
            properties['CAT'] = 'AD-INOP'
        if item['type'] == 9: # 9: Airport resp. Airfield IFR
            properties['CAT'] = 'AD'
        if item['type'] == 10: # 10: Airfield Water
            properties['CAT'] = 'AD-WATER'
        if item['type'] == 11: # 11: Landing Strip
            properties['CAT'] = 'AD'
        if item['type'] == 12: # 12: Agricultural Landing Strip
            properties['CAT'] = 'AD'
        if item['type'] == 13: # 13: Altiport
            properties['CAT'] = 'AD'
        
        if not 'CAT' in properties:
            continue

        # Get properties
        if 'ICAO' in item:
            properties['COD'] = item['ICAO']
            ADNames[item['ICAO']] = item['NAME']
        properties['ELE'] = item['elevation']['value']
        properties['NAM'] = item['name']
        properties['TYP'] = 'AD'

        """
        for frequency in item['frequencies']:
            name = ''
            if frequency['type'] == 0: # 0: Approach
                name = 'Approach ' + frequency['value']
            if frequency['type'] == 1: # 1: APRON
                name = 'Apron ' + frequency['value']
            if frequency['type'] == 2: # 2: Arrival
                name = 'Arrival ' + frequency['value']
            if frequency['type'] == 3: # 3: Center
                name = 'Center ' + frequency['value']
            if frequency['type'] == 4: # 4: CTAF
                name = 'CTAF ' + frequency['value']
            if frequency['type'] == 5: # 5: Delivery
                name = 'Delivery ' + frequency['value']
            if frequency['type'] == 6: # 6: Departure
                name = 'Departure ' + frequency['value']
            if frequency['type'] == 7: # 7: FIS
                name = 'FIS ' + frequency['value']
            if frequency['type'] == 8: # 8: Gliding
                name = 'Gliding ' + frequency['value']
            if frequency['type'] == 9: # 9: Ground
                name = 'Ground ' + frequency['value']
            if frequency['type'] == 10: # 10: Info
                name = 'Info ' + frequency['value']
            if frequency['type'] == 11: # 11: Multicom
                name = 'Multicom ' + frequency['value']
            if frequency['type'] == 12: # 12: Unicom
                name = 'Unicom ' + frequency['value']
            if frequency['type'] == 13: # 13: Radar
                name = 'Radar ' + frequency['value']
            if frequency['type'] == 14: # 14: Tower
                name = 'Tower ' + frequency['value']
            if frequency['type'] == 15: # 15: ATIS
                name = 'ATIS ' + frequency['value']
            if frequency['type'] == 16: # 16: Radio
                name = 'Radio ' + frequency['value']
            if frequency['type'] == 17: # 17: AIRMET
                name = 'AIRMET ' + frequency['value']
            if frequency['type'] == 18: # 18: AWOS
                name = 'AWOS ' + frequency['value']
            if frequency['type'] == 19: # 19: Lights
                name = 'Lights ' + frequency['value']
            if frequency['type'] == 20: # 20: VOLMET
                name = 'VOLMET ' + frequency['value']

            if 'name' in frequency:
                print(frequency['name'])
            print(frequency['value'])
        print(properties)
        exit(-1)

        INF = ""
        COMs = []
        NAV = ""
        OTH = ""
        for radio in airport.findall('RADIO'):
            if radio.find('FREQUENCY').text == None:
                continue

            if radio.get('CATEGORY') == 'INFORMATION':
                if radio.find('DESCRIPTION') != None:
                    INF += radio.find('DESCRIPTION').text
                else:
                    INF += radio.find('TYPE').text
                INF += " " + radio.find('FREQUENCY').text + " MHz\n"
            if radio.get('CATEGORY') == 'COMMUNICATION':
                COM = ""
                if radio.find('DESCRIPTION') != None:
                    COM += radio.find('DESCRIPTION').text
                else:
                    COM += radio.find('TYPE').text
                COM += " " + radio.find('FREQUENCY').text + " MHz"
                COMs.append(COM)
                if (airport.find('ICAO') != None) and (airport.find('ICAO').text not in ADFrequencies) and ('TWR' in COM.upper() or 'TOWER' in COM.upper()):
                    ADFrequencies[airport.find('ICAO').text] = COM
            if radio.get('CATEGORY') == 'NAVIGATION':
                if radio.find('DESCRIPTION') != None:
                    NAV += radio.find('DESCRIPTION').text
                else:
                    NAV += radio.find('TYPE').text
                NAV += " " + radio.find('FREQUENCY').text + " MHz\n"
            if radio.get('CATEGORY') == 'OTHER':
                if radio.find('DESCRIPTION') != None:
                    OTH += radio.find('DESCRIPTION').text
                else:
                    OTH += radio.find('TYPE').text
                OTH += " " + radio.find('FREQUENCY').text + " MHz\n"


        if INF != "":
            properties['INF'] = INF[0:-1]
        if COMs != []:
            # Need to sort frequencies: TWR first, then GROUND, then APRON, then all others
            COMsSorted = sorted([com for com in COMs if ('TWR' in com.upper() or 'TOWER' in com.upper())])
            COMs = [ com for com in COMs if com not in COMsSorted]
            COMsSorted += sorted([ com for com in COMs if 'GND' in com.upper() or 'GROUND' in com.upper()])
            COMs = [ com for com in COMs if com not in COMsSorted]
            COMsSorted += sorted(COMs)
            properties['COM'] = '\n'.join(COMsSorted)
        if NAV != "":
            properties['NAV'] = NAV[0:-1]
        if OTH != "":
            properties['OTH'] = OTH[0:-1]

        # Get runways
        RWYs = []
        bestRWY_isPaved = False
        bestRWY_dir     = 0.0
        bestRWY_found   = False
        bestRWY_len     = 0.0
        for rwy in airport.findall("./RWY[@OPERATIONS='ACTIVE']"):
            descr = rwy.find('NAME').text + ", " + str(round(float(rwy.find('LENGTH').text))) + "×" + str(round(float(rwy.find('WIDTH').text))) + "m, "
            if rwy.find('SFC').text != None:
                descr += rwy.find('SFC').text + ", "
            descr += rwy.find('DIRECTION').get('TC') + "°"
            RWYs.append(descr)
            RWYsIsPaved = rwy.find('SFC').text in ["ASPH", "CONC"]

            if RWYsIsPaved and not bestRWY_isPaved:
                bestRWY_isPaved = RWYsIsPaved
                bestRWY_dir     = float(rwy.find('DIRECTION').get('TC'))
                bestRWY_found   = True
                bestRWY_len     = float(rwy.find('LENGTH').text)

            if (RWYsIsPaved == bestRWY_isPaved) and (float(rwy.find('LENGTH').text) > bestRWY_len):
                bestRWY_isPaved = RWYsIsPaved
                bestRWY_dir     = float(rwy.find('DIRECTION').get('TC'))
                bestRWY_found   = True
                bestRWY_len     = float(rwy.find('LENGTH').text)

        if bestRWY_found:
            if properties['CAT'] in ['AD', 'AD-MIL']:
                if bestRWY_isPaved:
                    properties['CAT'] = properties['CAT']+'-PAVED'
                else:
                    properties['CAT'] = properties['CAT']+'-GRASS'

        if RWYs != []:
            properties['RWY'] = '\n'.join(RWYs)
            properties['ORI'] = bestRWY_dir

        # Get geometry
        lat = airport.find('GEOLOCATION').find('LAT').text
        lon = airport.find('GEOLOCATION').find('LON').text
        coordinate = [ round(float(lon), numCoordDigits), round(float(lat), numCoordDigits) ]
        """

        # Get further properties
        properties['TYP'] = 'AD'
        
        #
        # Generate feature
        #
        feature = {'type': 'Feature'}
        feature['geometry'] = item['geometry']
        feature['properties'] = properties
        features.append(feature)

    return features


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
        # If CAT has not yet been assigned, look at the ICAO class of the airspace
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

        # Get further properties
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
