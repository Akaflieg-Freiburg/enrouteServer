#!/usr/bin/python3

import json
import os.path
import re
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
    if verbose:
        print(': Read airspaces')
    for airspace in root.findall('./AIRSPACES/ASP'):
        if verbose:
            print('')
            print(': -- Airspace')
            ET.dump(airspace)
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

# OFMX Tools

def readOFMXHeight(xmlNode, ending):
    """Read height information

    In OFMX, height information for X in an xmlNode is usually specified by
    three subnodes, called "codeDistVerX", "uomDistVerX" and "valDistVerX".
    This method looks for these subnodes and interprets their content. If ALL
    goes well, it returns a string such as "GND", "100 FT GND", "2300 FT MSL" or
    "FL 95". If the data is not found or cannot be interpreted, an empty string
    is returned.
    """

    # Code - this is STD (=flight level), HEI (=height over ground), ALT (=height over MSL)
    if xmlNode.find('codeDistVer'+ending) == None:
        return "";
    codeDistVer = xmlNode.find('codeDistVer'+ending).text
    if codeDistVer == None:
        return "";
    if (codeDistVer != 'STD') and (codeDistVer != 'HEI') and (codeDistVer != 'ALT'):
        print("Error in readOFMXHeight codeDistVer is " + codeDistVer)
        exit(-1)

    # Read units of measurement - this is FL (=flight level), FT (=feet), M (=meters)
    if xmlNode.find('uomDistVer'+ending) == None:
        return "";
    uomDistVer = xmlNode.find('uomDistVer'+ending).text
    if uomDistVer == None:
        return "";
    if (uomDistVer != 'FL') and (uomDistVer != 'FT') and (uomDistVer != 'M'):
        print("Error in readOFMXHeight uomDistVer is " + uomDistVer)
        exit(-1)

    if xmlNode.find('valDistVer'+ending) == None:
        return "";
    valDistVer = xmlNode.find('valDistVer'+ending).text
    if valDistVer == None:
        return "";
    if valDistVer == '':
        return "";

    try:
        valDistVerINT = int(valDistVer)
    except:
        print("Warning: Cannot interpret number '{}' in {}".format(valDistVer, xmlNode.find('PrcUid').attrib))

    result = ""
    if uomDistVer == 'FL':
        result = "FL " + valDistVer
    else:
        result = valDistVer + " " + uomDistVer
        if codeDistVer == "HEI":
            result = result + " GND"
        if codeDistVer == "ALT":
            result = result + " MSL"
    if (codeDistVer == "HEI") and (valDistVer == "0"):
        return "GND"
    return result

def readOFMXHeight4GeoJSON(xmlNode, ending):
    """Read height information

    In OFMX, height information for X in an xmlNode is usually specified by
    three subnodes, called "codeDistVerX", "uomDistVerX" and "valDistVerX".
    This method looks for these subnodes and interprets their content. If ALL
    goes well, it returns a string such as specified here:
    https://github.com/Akaflieg-Freiburg/enrouteServer/wiki/GeoJSON-files-used-in-enroute-flight-navigation#typ-as-airspaces
    that is, of the form "GND", "1000 AGL", "2300" or "FL 95". If the data is
    not found or cannot be interpreted, an empty string is returned.
    """

    # Code - this is STD (=flight level), HEI (=height over ground), ALT (=height over MSL)
    if xmlNode.find('codeDistVer'+ending) == None:
        return "";
    codeDistVer = xmlNode.find('codeDistVer'+ending).text
    if codeDistVer == None:
        return "";
    if (codeDistVer != 'STD') and (codeDistVer != 'HEI') and (codeDistVer != 'ALT'):
        print("Error in readOFMXHeight codeDistVer is " + codeDistVer)
        exit(-1)

    # Read units of measurement - this is FL (=flight level), FT (=feet), M (=meters)
    if xmlNode.find('uomDistVer'+ending) == None:
        return "";
    uomDistVer = xmlNode.find('uomDistVer'+ending).text
    if uomDistVer == None:
        return "";
    if (uomDistVer != 'FL') and (uomDistVer != 'FT') and (uomDistVer != 'M'):
        print("Error in readOFMXHeight uomDistVer is " + uomDistVer)
        exit(-1)

    if xmlNode.find('valDistVer'+ending) == None:
        return "";
    valDistVer = xmlNode.find('valDistVer'+ending).text
    if valDistVer == None:
        return "";
    if valDistVer == '':
        return "";

    try:
        valDistVerINT = int(valDistVer)
    except:
        print("Warning: Cannot interpret number '{}' in {}".format(valDistVer, xmlNode.find('PrcUid').attrib))

    if uomDistVer == 'FL':
        return "FL " + valDistVer
    if codeDistVer == "HEI":
        if valDistVer == "0":
            return "GND"
        return valDistVer + " AGL"
    if codeDistVer == "ALT":
        return valDistVer
    return ""

def readOFMXMinMaxHeight(xmlNode, minEnding, maxEnding):
    """Read height information - height bands

    In OFMX, height bands for VFR procedure for X in usually specified by
    six subnodes, called "codeDistVerXLower", "uomDistVerXLower",
    "valDistVerXLower", "codeDistVerXUpper", "uomDistVerXUpprt" and
    "valDistVerXUpper". This method looks for these subnodes and interprets
    their content. If ALL goes well, it returns a string such as
    "MIN. 100 FT GND", "MIN. 2500 FT MSL · MAX 4500 FT MSL". If the data is not
    found or cannot be interpreted, an empty string is returned.
    """

    lower = readOFMXHeight(xmlNode, 'Lower')
    upper = readOFMXHeight(xmlNode, 'Upper')
    if lower == upper:
        return lower
    result = ''
    if lower != "":
        result = result + "MIN. " + lower
    if upper != "":
        if result != "":
            result = result + " · "
        result = result + "MAX. " + upper
    return result

def readOFMXProcedures(root):
    #
    # Read all procedures
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
        if prc.find('_beztrajectory') == None:
            continue;
        if prc.find('_beztrajectory').find('gmlPosList') == None:
            continue;
        for coordinatePair in prc.find('_beztrajectory').find('gmlPosList').text.split():
            x = coordinatePair.split(',')
            coordinates.append([round(float(x[0]), numCoordDigits), round(float(x[1]), numCoordDigits)])
        feature['geometry'] = {'type': 'LineString', 'coordinates': coordinates}

        # Get text name
        txtName = prc.find('txtName').text

        # Check if height information is available. The information is pretty
        # hidden in OFMX, and the data extraction method varies, depending on
        # whether this is a traffic circuit or a vfr arrival, departure or
        # transit route.
        if prc.find('codeType').text == "TRAFFIC_CIRCUIT":
            # Get height - if procedure is TFC
            heightString = readOFMXHeight(prc, 'Tfc')
            if heightString != "":
                if txtName != "":
                    txtName = txtName + " • "
                txtName = txtName + heightString
        else:
            # Get height - if procedure is not TFC. In this case, the procedure
            # is subdivided into a number of legs, each with an entry and exit
            # location, and each location with a height band. This is WAY too
            # complicated for us. We show the height band only if all bands
            # for all locations of all legs agree. Otherwise, we show nothing.
            heightBands = set()
            for leg in prc.findall('Leg'):
                band = readOFMXMinMaxHeight(leg.find('entry'), 'Lower', 'Upper')
                heightBands.add(band)
                band = readOFMXMinMaxHeight(leg.find('exit'), 'Lower', 'Upper')
                heightBands.add(band)
            if (len(heightBands) == 1) and not "" in heightBands:
                if txtName != "":
                    txtName = txtName + " • "
                txtName = txtName + band

        # Setup properties
        properties = {'TYP': 'PRC', 'CAT': 'PRC', 'NAM': txtName}

        # Set properties depending on use case
        if prc.find('codeType').text == "TRAFFIC_CIRCUIT":
            if ("GLIDER" in txtName.upper()) or (re.search(r"\bUL\b", txtName.upper())):
                properties['GAC'] = "red"
            else:
                properties['GAC'] = "blue"
            properties['USE'] = "TFC"
        elif prc.find('codeType').text == "VFR_ARR":
            properties['GAC'] = "blue"
            properties['USE'] = "ARR"
        elif prc.find('codeType').text == "VFR_DEP":
            properties['GAC'] = "blue"
            properties['USE'] = "DEP"
        elif prc.find('codeType').text == "VFR_HOLD":
            properties['GAC'] = "blue"
            properties['USE'] = "HLD"
        elif prc.find('codeType').text == "VFR_TRANS":
            properties['GAC'] = "blue"
            properties['USE'] = "TRA"
        else:
            print("Unknown code type in procedure: {}".format(prc.find('codeType').text))
            exit(-1)

        feature['properties'] = properties

        # Feature is now complete. Add it to the 'features' array
        features.append(feature)

def readOFMXNRA(root, shapeRoot):
    for nra in root.findall("./Ase/AseUid[codeType='NRA']/.."):
        NraUid   = nra.find('AseUid')
        mid      = NraUid.get('mid')

        # Get geometry
        coordinates = []
        gmlPosList = shapeRoot.find("./Ase/AseUid[@mid='{}']/../gmlPosList".format(mid)).text
        for coordinateTripleString in gmlPosList.split():
            coordinateTriple = coordinateTripleString.split(",")
            coordinate = [ round(float(coordinateTriple[0]), numCoordDigits), round(float(coordinateTriple[1]), numCoordDigits) ]
            coordinates.append(coordinate)
        # Make sure the polygon closes
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])

        # Get properties
        properties = {}
        properties['BOT'] = readOFMXHeight4GeoJSON(nra, 'Lower')
        properties['CAT'] = 'NRA'
        properties['ID']  = mid
        properties['NAM'] = nra.find('txtName').text
        properties['TOP'] = readOFMXHeight4GeoJSON(nra, 'Upper')
        properties['TYP'] = "AS"

        # Generate feature
        feature = {'type': 'Feature'}
        feature['geometry'] = {'type': 'Polygon', 'coordinates': [coordinates]}
        feature['properties'] = properties
        features.append(feature)


def readOFMX(fileName, shapeFileName):
    print('Read OFMX…')
    tree = ET.parse(fileName)
    root = tree.getroot()

    shapeTree = ET.parse(shapeFileName)
    shapeRoot = shapeTree.getroot()

    # Read procedures
    readOFMXProcedures(root)

    # Read nature reserve areas
    readOFMXNRA(root, shapeRoot)

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
        feature['geometry'] = {'type': 'Point', 'coordinates': getCoordinate(DpnUid)}

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

def readNavaidsFromOFMX(fileName):
    print('Read OFMX for navaids…')
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
verbose = False

features = []

ADNames       = {}
ADFrequencies = {}
haveNav       = False

for arg in [arg for arg in sys.argv[1:] if arg.endswith('.aip')]:
    if arg.endswith('nav.aip'):
        if os.path.getsize(arg) != 0:
            haveNav = True
    readOpenAIP(arg)
for arg in [arg for arg in sys.argv[1:] if arg.endswith('.ofmx') and not arg.endswith('shape.ofmx')]:
    shapeFile = arg.replace(".ofmx", ".shape.ofmx")
    readOFMX(arg, shapeFile)
    if not haveNav:
        readNavaidsFromOFMX(arg)
for arg in [arg for arg in sys.argv[1:] if not arg.endswith(".aip") and not arg.endswith(".ofmx") and not arg.endswith(".aixm")]:
    print("Unknown file type {}".format(arg))
    exit(-1)


# Generate Feature Collection
featureCollection = {'type': 'FeatureCollection', 'features': features}

# Generate GeoJSON and write it to a file
geojson = json.dumps(featureCollection, sort_keys=True, separators=(',', ':'))
file = open('test.geojson', 'w')
file.write(geojson)
