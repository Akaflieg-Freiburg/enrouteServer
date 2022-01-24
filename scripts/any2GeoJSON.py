#!/usr/bin/python3

import json
import os.path
import re
import sys
import xml.etree.ElementTree as ET

import OFMX
import openAIP2

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


def interpretAltitudeLimit(limit):
    alt   = limit.find('ALT')
    if alt.text != None:
        altText = str(round(float(alt.text)))
    else:
        print("WARNING: Cannot interpret vertical airspace limit, assuming '0' as a default!")
        altText = "0"

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



# OFMX Tools

def readNavaidsFromOFMX(root, numCoordDigits):
    print('… Navaids')

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
        feature['geometry'] = {'type': 'Point', 'coordinates': OFMX.readCoordinate(VorUid, numCoordDigits)}

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
        feature['geometry'] = {'type': 'Point', 'coordinates': OFMX.readCoordinate(NdbUid, numCoordDigits)}

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


def readOFMX(fileName, shapeFileName, includeNavaids=False):
    global features

    print('Read and Interpret OFMX …')

    # Read XML of OFMX file
    tree = ET.parse(fileName)
    root = tree.getroot()
    sources.add("open flightmaps data for region {}, created {}".format(root.find('Ppa').find('PpaUid').attrib['region'], root.attrib['created']))

    # Read XML of OFMX shape file
    shapeTree = ET.parse(shapeFileName)
    shapeRoot = shapeTree.getroot()
    sources.add("open flightmaps shape extension data for region {}, created {}".format(root.find('Ppa').find('PpaUid').attrib['region'], shapeRoot.attrib['created']))

    # Read FIS Sectors
    features += OFMX.readFeatures_FISSectors(root, shapeRoot, numCoordDigits)

    # Read Nature Reserve Areas
    features += OFMX.readFeatures_NRA(root, shapeRoot, numCoordDigits)

    # Read Navaids
    if includeNavaids:
        readNavaidsFromOFMX(root, numCoordDigits)

    # Read Procedures
    features += OFMX.readFeatures_Procedures(root, numCoordDigits)


    #
    # Read all reporting points
    #
    for Dpn in root.findall('./Dpn'):
        if not Dpn.find("codeType").text in ["VFR-MRP", "VFR-RP"]:
            continue
        DpnUid   = Dpn.find('DpnUid')

        mid      = DpnUid.get('mid')
        WPcodeId = ""
        APcodeId = ""
        txtName  = ""

        if DpnUid.find('codeId').text != None:
            WPcodeId = DpnUid.find('codeId').text

        if Dpn.find('AhpUidAssoc') != None:
            if Dpn.find('AhpUidAssoc').find('codeId') != None:
                if Dpn.find('AhpUidAssoc').find('codeId').text != None:
                    APcodeId = Dpn.find('AhpUidAssoc').find('codeId').text

        if Dpn.find('txtName') != None:
            if Dpn.find('txtName').text != None:
                txtName = Dpn.find('txtName').text

        if txtName == "":
            print("Found Dpn without txtName. Exiting")
            exit(-1)

        if WPcodeId == "" and txtName != "":
            WPcodeId = txtName

        # Feature dictionary, will be filled in here and included into JSON
        feature = {'type': 'Feature'}

        # Position
        feature['geometry'] = {'type': 'Point', 'coordinates': OFMX.readCoordinate(DpnUid, numCoordDigits)}

        #
        # Properties
        #
        properties = {'TYP': 'WP'}
        properties['MID'] = DpnUid.get('mid')
        if Dpn.find("codeType").text == "VFR-MRP":
            properties['CAT'] = 'MRP'
        if Dpn.find("codeType").text == "VFR-RP":
            properties['CAT'] = 'RP'

        # Property: COD - required
        #
        # This property holds a code name of the waypoint, such as "EDDE-S1".
        # The **enroute** app uses this property for the ID field on the
        # waypoint description dialog.

        if APcodeId != "":
            properties['COD']  = APcodeId + "-" + WPcodeId
        else:
            properties['COD']  = WPcodeId

        # Property: COM - optional
        #
        # A string that describes an associated frequency, such as "EDDE - TWR
        # 121.150 MHz".

        if APcodeId != "" and APcodeId in ADFrequencies:
            properties['COM'] = APcodeId + " - " + ADFrequencies[APcodeId]

        # Property: ICA - optional
        #
        # A string with the ICAO code of an associated airfield, such as "EDDE".

        if APcodeId != "":
            properties['ICA'] = APcodeId

        # Property: MID - optional
        #
        # Internal ID of the waypoint in the AIXM database. This is a string
        # such as "7295".

        properties['MID'] = mid

        # Property: NAM - required
        #
        # Name of the waypoint, such as "ERFURT-WEIMAR (SIERRA1)".  The
        # **enroute** app uses this property for the title of the waypoint
        # description dialog.

        if APcodeId != "" and APcodeId in ADNames:
            fullName = ADNames[APcodeId]
            if txtName != "":
                fullName += " (" + txtName + ")"
            properties['NAM'] = fullName
        else:
            properties['NAM']  = txtName

        # Property: SCO - required for CAT == MRP and CAT == RP
        #
        # Short description of the waypoint, such as "S1".  The **enroute** app
        # uses this property for the display name of the point on the moving
        # map.

        properties['SCO'] = WPcodeId

        # Done with properties

        feature['properties'] = properties

        # Feature is now complete. Add it to the 'features' array
        features.append(feature)

#
# Main programm starts here
#

numCoordDigits = 5
verbose = False

features = []
sources = set() # Info about the maps used

ADNames       = {}
ADFrequencies = {}
haveNav       = False

# Read navaids
openAIPNavaids = openAIP2.readOpenAIPNavaids(sys.argv[1])
if openAIPNavaids:
    features = openAIPNavaids
    haveNav = True

# Read airspaces
openAIPAirspaces = openAIP2.readOpenAIPAirspaces(sys.argv[1])
if openAIPAirspaces:
    features += openAIPAirspaces

# Read airports
openAIPAirports = openAIP2.readOpenAIPAirports(sys.argv[1])
if openAIPAirports:
    features += openAIPAirports

for arg in [arg for arg in sys.argv[2:] if arg.endswith('.ofmx') and not arg.endswith('shape.ofmx')]:
    shapeFile = arg.replace(".ofmx", ".shape.ofmx")
    readOFMX(arg, shapeFile, not haveNav)
for arg in [arg for arg in sys.argv[2:] if not arg.endswith(".ofmx") and not arg.endswith(".aixm")]:
    print("Unknown file type {}".format(arg))
    exit(-1)

# Generare Info string
infoString = ""
for source in sources:
    infoString += source+";"
infoString = infoString[0:-1]

# Generate Feature Collection
featureCollection = {'type': 'FeatureCollection', 'info': infoString, 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('test.geojson', 'w')
file.write(geojson)
