#!/bin/python

"""
openAIP2
=======================================================================================================

Toolset to read aviation data from the openAIP2 web site and to transform the
data into the GeoJSON format described here:
https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation
"""

import json
import math
import re
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


def downloadOpenAIPData(typeName):
    """Read data from the openAIP2 API.

    :param typeName: Name data ("navaids")

    :returns: array with data items

    """

    page = 1
    totalPages = 1.0
    items = []
    while page <= math.ceil(totalPages):
        my_headers = {'x-openaip-client-id' : os.environ['openAIP']}
        try:
            response = requests.get("https://api.core.openaip.net/api/"+typeName, headers=my_headers, params={'limit': 1000, 'page': page} )
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

        if page == 1:
            print("Reading openAIP " + typeName + ", " + str(parsedResponse['totalCount']) + " items")

        items.extend(parsedResponse['items'])
        totalPages = float(parsedResponse['totalCount'])/float(parsedResponse['limit'])
        page = page + 1

    return items


def readOpenAIPAirports(airportData):
    """Read airspaces from the openAIP2 API.

    :param airportData: Data about airports, as downloaded from openAIP

    :returns: GeoJSON feature array, in the format described here:
        https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    print("Interpreting airport data…")
    features = []
    for item in airportData:
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
        if 'icaoCode' in item:
            properties['COD'] = item['icaoCode']
        properties['ELE'] = item['elevation']['value']
        properties['NAM'] = item['name']
        properties['TYP'] = 'AD'

        if 'frequencies' in item:
            INF = ""
            COMs = []
            NAV = ""
            OTH = ""

            for frequency in item['frequencies']:
                name = ''
                type = ''
                if frequency['type'] == 0: # 0: Approach
                    name = 'Approach'
                    type = 'COM'
                if frequency['type'] == 1: # 1: APRON
                    name = 'Apron'
                    type = 'COM'
                if frequency['type'] == 2: # 2: Arrival
                    name = 'Arrival'
                    type = 'COM'
                if frequency['type'] == 3: # 3: Center
                    name = 'Center'
                    type = 'COM'
                if frequency['type'] == 4: # 4: CTAF
                    name = 'CTAF'
                    type = 'COM'
                if frequency['type'] == 5: # 5: Delivery
                    name = 'Delivery'
                    type = 'COM'
                if frequency['type'] == 6: # 6: Departure
                    name = 'Departure'
                    type = 'COM'
                if frequency['type'] == 7: # 7: FIS
                    name = 'FIS'
                    type = 'COM'
                if frequency['type'] == 8: # 8: Gliding
                    name = 'Gliding'
                    type = 'COM'
                if frequency['type'] == 9: # 9: Ground
                    name = 'Ground'
                    type = 'COM'
                if frequency['type'] == 10: # 10: Info
                    name = 'Info'
                    type = 'COM'
                if frequency['type'] == 11: # 11: Multicom
                    name = 'Multicom'
                    type = 'COM'
                if frequency['type'] == 12: # 12: Unicom
                    name = 'Unicom'
                    type = 'COM'
                if frequency['type'] == 13: # 13: Radar
                    name = 'Radar'
                    type = 'COM'
                if frequency['type'] == 14: # 14: Tower
                    name = 'Tower'
                    type = 'COM'
                if frequency['type'] == 15: # 15: ATIS
                    name = 'ATIS'
                    type = 'INFO'
                if frequency['type'] == 16: # 16: Radio
                    name = 'Radio'
                    type = 'COM'
                if frequency['type'] == 17: # 17: Other
                    name = 'Other'
                    type = 'COM'
                if frequency['type'] == 18: # 18: AIRMET
                    name = 'AIRMET'
                    type = 'INFO'
                if frequency['type'] == 19: # 19: AWOS
                    name = 'AWOS'
                    type = 'INFO'
                if frequency['type'] == 20: # 20: Light
                    name = 'Lights'
                    type = 'OTH'
                if frequency['type'] == 21: # 21: VOLMET
                    name = 'VOLMET'
                    type = 'INFO'

                if 'name' in frequency:
                    name = frequency['name']
                if not frequency['value'] in name:
                    name = name + ' ' + frequency['value'] + ' MHz'

                if type == 'COM':
                    COMs.append(name)
                if type == 'INFO':
                    INF += name + '\n'
                if type == 'OTH':
                    OTH += name + '\n'

            if COMs != []:
                # Need to sort frequencies: TWR first, then GROUND, then APRON, then all others
                COMsSorted = sorted([com for com in COMs if ('TWR' in com.upper() or 'TOWER' in com.upper())])
                COMs = [ com for com in COMs if com not in COMsSorted]
                COMsSorted += sorted([ com for com in COMs if 'GND' in com.upper() or 'GROUND' in com.upper()])
                COMs = [ com for com in COMs if com not in COMsSorted]
                COMsSorted += sorted(COMs)
                properties['COM'] = '\n'.join(COMsSorted)
            if INF != "":
                properties['INF'] = INF[0:-1]
            if NAV != "":
                properties['NAV'] = NAV[0:-1]
            if OTH != "":
                properties['OTH'] = OTH[0:-1]

        if 'runways' in item:
            RWYs = []
            bestRWY_isPaved = False
            bestRWY_dir     = 0.0
            bestRWY_found   = False
            bestRWY_len     = 0.0

            for runway in item['runways']:
                description = runway['designator']
                description += ' • ' + str(runway['dimension']['length']['value']) + '×' + str(runway['dimension']['width']['value']) + 'm'
                if runway['operations'] == 1:
                    description += ' • temporarily closed'
                if runway['operations'] == 2:
                    description += ' • closed'
                if 'condition' in  runway['surface']:
                    if runway['surface']['condition'] == 2:
                        description += ' • poor condition'
                    if runway['surface']['condition'] == 3:
                        description += ' • unsafe condition'
                    if runway['surface']['condition'] == 4:
                        description += ' • deformed'
                paved = False
                if 'mainComposite' in runway['surface']:
                    if runway['surface']['mainComposite'] == 0:
                        description += ' • ASPH'
                        paved = True
                    if runway['surface']['mainComposite'] == 1:
                        description += ' • CONC'
                        paved = True
                    if runway['surface']['mainComposite'] == 2:
                        description += ' • GRASS'
                    if runway['surface']['mainComposite'] == 3:
                        description += ' • SAND'
                    if runway['surface']['mainComposite'] == 4:
                        description += ' • WATER'
                    if runway['surface']['mainComposite'] == 5:
                        description += ' • TAR'
                    if runway['surface']['mainComposite'] == 6:
                        description += ' • BRICK'
                    if runway['surface']['mainComposite'] == 7:
                        description += ' • MACAM'
                    if runway['surface']['mainComposite'] == 8:
                        description += ' • STONE'
                    if runway['surface']['mainComposite'] == 9:
                        description += ' • CORAL'
                    if runway['surface']['mainComposite'] == 10:
                        description += ' • CLAY'
                    if runway['surface']['mainComposite'] == 11:
                        description += ' • LATERITE'
                    if runway['surface']['mainComposite'] == 12:
                        description += ' • GRAVEL'
                    if runway['surface']['mainComposite'] == 13:
                        description += ' • EARTH'
                    if runway['surface']['mainComposite'] == 14:
                        description += ' • ICE'
                    if runway['surface']['mainComposite'] == 15:
                        description += ' • SNOW'
                    if runway['surface']['mainComposite'] == 16:
                        description += ' • RUBBER'
                    if runway['surface']['mainComposite'] == 17:
                        description += ' • METAL'
                    if runway['surface']['mainComposite'] == 19:
                        description += ' • STEEL'
                    if runway['surface']['mainComposite'] == 20:
                        description += ' • WOOD'
                description += ' • ' + str(runway['trueHeading']) + '°'
                RWYs.append(description)
                if paved and not bestRWY_isPaved:
                    bestRWY_isPaved = True
                    bestRWY_dir     = runway['trueHeading']
                    bestRWY_found   = True
                    bestRWY_len     = runway['dimension']['length']['value']
                if (paved == bestRWY_isPaved) and (runway['dimension']['length']['value'] > bestRWY_len):
                    bestRWY_isPaved = paved
                    bestRWY_dir     = runway['trueHeading']
                    bestRWY_found   = True
                    bestRWY_len     = runway['dimension']['length']['value']

            if RWYs != []:
                properties['ORI'] = bestRWY_dir
                properties['RWY'] = '\n'.join(RWYs)
                if properties['CAT'] in ['AD', 'AD-MIL']:
                    if bestRWY_isPaved:
                        properties['CAT'] = properties['CAT']+'-PAVED'
                    else:
                        properties['CAT'] = properties['CAT']+'-GRASS'
           
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


def readOpenAIPAirspaces():
    """Read airspaces from the openAIP2 API.

    :returns: GeoJSON feature array, in the format described here:
        https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    items = downloadOpenAIPData('airspaces')
    print("Interpreting airspace data…")
    features = []
    for item in items:

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
        # 26: Controlled Area (CTA)
        # 27: ACC Sector (ACC)
        if item['type'] == 28: # 28: Aerial Sporting Or Recreational Activity
            if 'PARA' in item['name']:
                properties['CAT'] = 'PJE'
        if item['type'] == 29: # 29: Low Altitude Overflight Restriction
            properties['CAT'] = 'R'

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
                properties['CAT'] = 'D'
            if item['icaoClass'] == 4: # E
                properties['CAT'] = 'E'
            if item['icaoClass'] == 5: # F
                properties['CAT'] = 'F'
            if item['icaoClass'] == 6: # G
                properties['CAT'] = 'G'

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


def readOpenAIPNavaids():
    """Read navaids from the openAIP2 API.

    :returns: GeoJSON feature array, in the format described here:
        https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    items = downloadOpenAIPData('navaids')
    print("Interpreting navaid data…")
    features = []
    for item in items:
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

def readOpenAIPReportingPoints(airportData):
    """Read reporting points from the openAIP2 API.

    :param airportData: Data about airports, as downloaded from openAIP

    :returns: GeoJSON feature array, in the format described here:
        https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    ICAOAlpha = ["ALFA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT", "GOLF", "HOTEL", "INDIA", "JULIETT", "KILO", "LIMA", "MIKE", "NOVEMBER", "OSCAR", "PAPA", "QUEBEC", "ROMEO", "SIERRA", "TANGO", "UNIFORM", "VICTOR", "WHISKEY", "X-RAY", "YANKEE", "ZULU"]

    airportCodes = {} # ICAO Codes by _id
    airportNames = {} # Airport names by _id
    for airport in airportData:
        id = airport['_id']
        if 'icaoCode' in airport:
            airportCodes[id] = airport['icaoCode']
        airportNames[id] = airport['name']

    items = downloadOpenAIPData('reporting-points')
    print("Interpreting reporting-points data…")
    features = []
    for item in items:
        id = item['airports'][0]

        #
        # Get properties
        #
        properties = {}
        properties['TYP'] = "WP"

        if item['compulsory']:
            properties['CAT'] = "MRP"
        else:
            properties['CAT'] = "RP"
        properties['NAM'] = airportNames[id]+" ("+item['name']+")"
        SCO = item['name']
        for letter in ICAOAlpha:
            SCO = re.sub(r'\b'+letter+r'\b', letter[0], SCO)
        properties['SCO'] = SCO
        if id in airportCodes:
            properties['COD'] = airportCodes[id]+"-"+SCO
            properties['ICA'] = airportCodes[id]
        else:
            properties['COD'] = SCO
        print(properties['COD'])

        #
        # Generate feature
        #
        feature = {'type': 'Feature'}
        feature['geometry'] = item['geometry']
        feature['properties'] = properties
        features.append(feature)

    return features


def readOpenAIP():
    """Read complete database from the openAIP2 API.

    :returns: GeoJSON feature array, in the format described here:
        https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation

    """

    airportData = downloadOpenAIPData('airports')

    features = []
    features += readOpenAIPReportingPoints(airportData)
    features += readOpenAIPAirports(airportData)
    features += readOpenAIPAirspaces()
    features += readOpenAIPNavaids()
    return features
