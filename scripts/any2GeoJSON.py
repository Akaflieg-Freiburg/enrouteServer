#!/usr/bin/python3

import json
import os.path
import sys
import xml.etree.ElementTree as ET

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



# Takes an XML node, looks for children with name 'geoLat' and 'geoLong', reads
# an interprets coordinates and returns array with latitude and longitude as
# floats

def getCoordinate(xmlNode):
    longText = xmlNode.find('geoLong').text
    if longText[-1] == 'E':
        long = longText[-100:-1]
    if longText[-1] == 'W':
        long = "-" + longText[-100:-1]
    
    latText = xmlNode.find('geoLat').text
    if latText[-1] == 'N':
        lat = latText[-100:-1]
    if latText[-1] == 'S':
        lat = "-" + latText[-100:-1]
    
    return [round(float(long), numCoordDigits), round(float(lat), numCoordDigits)]


def interpretAltitudeLimit(limit):
    alt   = limit.find('ALT')
    altText = str(round(float(alt.text)))
    if alt.get('UNIT') == "FL":
        return "FL " + altText 
    if alt.get('UNIT') != "F":
        print("Error")
        exit(-1)
    
    if limit.get('REFERENCE') == "MSL":
        return altText
    if alt.text == "0":
        return "GND"
    return altText + " AGL"
    
# XXX

def readOpenAIP(fileName):
    # Safety check
    if os.path.getsize(fileName) == 0:
        print('File {} is empty! Ignoring file…'.format(fileName))
        return
        
    print('Read openAIP file {}…'.format(fileName))
    tree = ET.parse(fileName)
    root = tree.getroot()

    #
    # Read airfields
    #
    for airport in root.findall('./WAYPOINTS/AIRPORT'):
        
        # Ignore the following airfields
        if airport.get('TYPE') in ["HELI_CIVIL", "HELI_MIL", ""]:
            continue
        
        # Get properties
        properties = {}
        if airport.get('TYPE') == 'AD_CLOSED':
            properties['CAT'] = 'AD-INOP'
        elif airport.get('TYPE') == 'GLIDING':
            properties['CAT'] = 'AD-GLD'
        elif airport.get('TYPE') == 'AD_MIL':
            properties['CAT'] = 'AD-MIL'
        elif airport.get('TYPE') == 'LIGHT_AIRCRAFT':
            properties['CAT'] = 'AD-UL'
        elif airport.get('TYPE') == 'AF_WATER':
            properties['CAT'] = 'AD-WATER'
        else:
            properties['CAT'] = 'AD'

        if airport.find('ICAO') != None:
            properties['COD'] = airport.find('ICAO').text
            ADNames[airport.find('ICAO').text] = airport.find('NAME').text
        properties['ELE'] = round(float(airport.find('GEOLOCATION').find('ELEV').text))
        properties['NAM'] = airport.find('NAME').text
        properties['TYP'] = 'AD'

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

        # Generate feature
        feature = {'type': 'Feature'}
        feature['geometry'] = {'type': 'Point', 'coordinates': coordinate}
        feature['properties'] = properties
        features.append(feature)
        
    
    #
    # Read navaids
    #
    for navaid in root.findall('./NAVAIDS/NAVAID'):

        # Ignore the following navaids
        if navaid.get('TYPE') in ["DME", "TACAN"]:
            continue

        # Warning
        if navaid.find('RADIO').find('FREQUENCY').text == None:
            print("WARNING: Navaid " + navaid.find('NAME').text + " without frequency!")
            continue
        
        # Get properties
        properties = {}
        properties['CAT'] = navaid.get('TYPE')
        properties['COD'] = navaid.find('ID').text
        properties['ELE'] = round(float(navaid.find('GEOLOCATION').find('ELEV').text))
        properties['NAM'] = navaid.find('NAME').text
        properties['MOR'] = morse(navaid.find('ID').text)
        freq = navaid.find('RADIO').find('FREQUENCY').text
        if navaid.get('TYPE') == "NDB":
            freq += " kHz"
        else:
            freq += " MHz"
        if navaid.find('RADIO').find('CHANNEL') != None:
            freq += " • " + navaid.find('RADIO').find('CHANNEL').text
        properties['NAV'] = freq
        properties['TYP'] = 'NAV'

        # Get geometry
        lat =  navaid.find('GEOLOCATION').find('LAT').text
        lon =  navaid.find('GEOLOCATION').find('LON').text
        coordinate = [ round(float(lon), numCoordDigits), round(float(lat), numCoordDigits) ]

        # Generate feature
        feature = {'type': 'Feature'}
        feature['geometry'] = {'type': 'Point', 'coordinates': coordinate}
        feature['properties'] = properties
        features.append(feature)


    #
    # Read airspaces
    #
    for airspace in root.findall('./AIRSPACES/ASP'):
        
        # Ignore the following airspaces
        if airspace.get('CATEGORY') in ["E", "F", "FIR", "GLIDING", "G", "OTH", "UIR", "WAVE"]:
            continue
        if airspace.get('CATEGORY') in ["TMA"]:
            print("TMA")
            exit(-1)

        # Get geometry
        coordinates = []
        for cooPair in airspace.find('GEOMETRY').find('POLYGON').text.split(','):
            cooPairArray = cooPair.split()
            coordinate = [ round(float(cooPairArray[0]), numCoordDigits), round(float(cooPairArray[1]), numCoordDigits) ]
            coordinates.append(coordinate)
        
        # Get properties
        properties = {}
        properties['BOT'] = interpretAltitudeLimit(airspace.find('ALTLIMIT_BOTTOM'))
        if airspace.get('CATEGORY') == 'DANGER':
            if airspace.find('NAME').text.startswith('PARA'):
                properties['CAT'] = 'PJE'
            else:
                properties['CAT'] = 'DNG'
        elif airspace.get('CATEGORY') == 'PROHIBITED':
            properties['CAT'] = 'P'
        elif airspace.get('CATEGORY') == 'RESTRICTED':
            properties['CAT'] = 'R'
        else:
            properties['CAT'] = airspace.get('CATEGORY')
        properties['ID']  =  airspace.find('ID').text
        properties['NAM'] = airspace.find('NAME').text
        properties['TOP'] = interpretAltitudeLimit(airspace.find('ALTLIMIT_TOP'))
        properties['TYP'] = "AS"

        # Generate feature
        feature = {'type': 'Feature'}
        feature['geometry'] = {'type': 'Polygon', 'coordinates': [coordinates]}
        feature['properties'] = properties
        features.append(feature)



def readOFMX(fileName):
    print('Read OFMX…')
    tree = ET.parse(fileName)
    root = tree.getroot()


    #
    # Find all procedures
    #
    for prc in root.findall('./Prc'):
        PrcUid = prc.find('PrcUid')

        if (prc.find('codeType').text != "TRAFFIC_CIRCUIT") and ("VFR" not in prc.find('codeType').text):
            continue;
        if prc.find('usageType') != None:
            if prc.find('usageType').text != "FIXED_WING":
                continue;

        # Feature dictionary, will be filled in here and included into JSON
        feature = {'type': 'Feature'}

        # Get geometry
        coordinates = []
        if prc.find('beztrajectory') == None:
            continue;
        if prc.find('beztrajectory').find('gmlPosList') == None:
            continue;
        for coordinatePair in prc.find('beztrajectory').find('gmlPosList').text.split():
            x = coordinatePair.split(',')
            coordinates.append([round(float(x[0]), numCoordDigits), round(float(x[1]), numCoordDigits)])
        feature['geometry'] = {'type': 'LineString', 'coordinates': coordinates}

        txtName = prc.find('txtName').text
        properties = {'TYP': 'PRC', 'CAT': 'PRC', 'NAM': txtName}
        if ("GLIDER" in txtName.upper()) or ("UL" in txtName.upper()):
            properties['GAC'] = "red"
        else:
            properties['GAC'] = "green"
        feature['properties'] = properties        

        # Feature is now complete. Add it to the 'features' array
        features.append(feature)
        

    #
    # Interpret all reporting points
    #
    for dpn in root.findall('./Dpn'):
        if not dpn.find("codeType").text in ["VFR-MRP", "VFR-RP"]:
            continue

        DpnUid = dpn.find('DpnUid')
        mid = DpnUid.get('mid')

        # Feature dictionary, will be filled in here and included into JSON
        feature = {'type': 'Feature'}
       
        # Position
        feature['geometry'] = {'type': 'Point', 'coordinates': getCoordinate(DpnUid)}
        
        # Properties
        properties = {'TYP': 'WP'}
        properties['MID'] = DpnUid.get('mid')
        if dpn.find("codeType").text == "VFR-MRP":
            properties['CAT'] = 'MRP'
        if dpn.find("codeType").text == "VFR-RP":
            properties['CAT'] = 'RP'
        
        if dpn.find('AhpUid_codeId') != None:
            properties['ICA'] = dpn.find('AhpUid_codeId').text

        if dpn.find('AhpUid_codeId') != None:
            if dpn.find('AhpUid_codeId').text in ADNames:
                fullName = ADNames[dpn.find('AhpUid_codeId').text]
                if (dpn.find('txtName') != None) and (dpn.find('txtName').text != None):
                    fullName += " (" + dpn.find('txtName').text + ")"
                properties['NAM'] = fullName
            if dpn.find('AhpUid_codeId').text in ADFrequencies:
                properties['COM'] = dpn.find('AhpUid_codeId').text + " - " + ADFrequencies[dpn.find('AhpUid_codeId').text]
        else:
            properties['NAM']  = DpnUid.find('codeId').text

        if dpn.find('AhpUid_codeId') != None and dpn.find('AhpUid_codeId').text != None:
            if DpnUid.find('codeId').text != None:
                properties['COD']  = dpn.find('AhpUid_codeId').text + "-" + DpnUid.find('codeId').text
            else:
                properties['COD']  = dpn.find('AhpUid_codeId').text + "-" + dpn.find('txtName').text
        if DpnUid.find('codeId').text != None:
            properties['SCO'] = DpnUid.find('codeId').text
        else:
            properties['SCO'] = dpn.find('txtName').text
        if ('NAM' not in properties) and ('COD' in properties):
            properties['NAM'] = properties['COD']
        if ('NAM' not in properties) and ('SCO' in properties):
            properties['NAM'] = properties['SCO']
        if 'NAM' not in properties:
            print('Error. Cannot find name for Waypoint')
            exit(-1)
            
            
        feature['properties'] = properties
        
        # Feature is now complete. Add it to the 'features' array
        features.append(feature)




def readNavaidsFromOFMX(fileName):
    print('Read AIXM for navaids…')
    tree = ET.parse(fileName)
    root = tree.getroot()

    #
    # Interpret all VOR Nodes
    #
    for vor in root.findall('./Vor'):
        VorUid = vor.find('VorUid')

        # Feature dictionary, will be filled in here and included into JSON
        feature = {'type': 'Feature'}

        # Find all associated DMEs
        dmes = root.findall("./Dme/VorUid[@mid='"+VorUid.get('mid')+"']")

        # Position
        feature['geometry'] = {'type': 'Point', 'coordinates': getCoordinate(VorUid)}

        # Properties
        properties = {'TYP': 'NAV'}
        if dmes == []:
            properties['CAT'] = 'VOR'
        else:
            properties['CAT'] = 'VOR-DME'
        properties['MID'] = VorUid.get('mid')
        if VorUid.find('txtName') != None and VorUid.find('txtName').text != None:
            properties['NAM'] = VorUid.find('txtName').text
        else:
            properties['NAM'] = VorUid.find('codeId').text
        properties['COD'] = VorUid.find('codeId').text
        properties['MOR'] = morse(VorUid.find('codeId').text)
        properties['NAV'] = vor.find('valFreq').text + " " + vor.find('uomFreq').text
        feature['properties'] = properties

        # Feature is now complete. Add it to the 'features' array
        features.append(feature)


    #
    # Interpret all NDB Nodes
    #

    for ndb in root.findall('./Ndb'):
        NdbUid = ndb.find('NdbUid')

        # Feature dictionary, will be filled in here and included into JSON
        feature = {'type': 'Feature'}

        # Position
        feature['geometry'] = {'type': 'Point', 'coordinates': getCoordinate(NdbUid)}

        # Properties
        properties = {'TYP': 'NAV', 'CAT': 'NDB'}
        properties['MID'] = ndb.get('mid')
        if ndb.find('txtName') != None and ndb.find('txtName').text != None:
            properties['NAM'] = ndb.find('txtName').text
        else:
            properties['NAM'] = NdbUid.find('codeId').text
        properties['COD'] = NdbUid.find('codeId').text
        properties['MOR'] = morse(NdbUid.find('codeId').text)
        properties['NAV'] = ndb.find('valFreq').text + " " + ndb.find('uomFreq').text

        # Feature is now complete. Add it to the 'features' array
        features.append(feature)

#
# Main programm starts here
#

numCoordDigits = 5

features = []

ADNames       = {}
ADFrequencies = {}
haveNav       = False

for arg in [arg for arg in sys.argv[1:] if arg.endswith('.aip')]:
    if arg.endswith('nav.aip'):
        if os.path.getsize(arg) != 0:
            haveNav = True
    readOpenAIP(arg)
for arg in [arg for arg in sys.argv[1:] if arg.endswith('.ofmx')]:
    readOFMX(arg)
    if not haveNav:
        readNavaidsFromOFMX(arg)    
for arg in [arg for arg in sys.argv[1:] if not arg.endswith(".aip") and not arg.endswith(".ofmx")]:
    print("Unknown file type {}".format(arg))
    exit(-1)

    
# Generate Feature Collection
featureCollection = {'type': 'FeatureCollection', 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('test.geojson', 'w')
file.write(geojson)
