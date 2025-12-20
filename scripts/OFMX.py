#!/bin/python3

"""
OFMX
====================================
Tools to interpret ofmx files
"""


import datetime
import re
import requests
import xml.etree.ElementTree as ET


regions = [
    #
    # Africa
    #
    ["fa",   "Africa/South Africa", "za"],
    ["fywh", "Africa/Namibia", "na"],
    #
    # Europe - EU27
    #
    ["lovv", "Europe/Austria", "at"],
    ["ebbu", "Europe/Belgium", "be"],
    ["lbsr", "Europe/Bulgaria", "bg"],
    ["ldzo", "Europe/Croatia", "hr"],
    ["lkaa", "Europe/Czech Republic", "cz"],
    ["ekdk", "Europe/Denmark", "dk"],
    ["efin", "Europe/Finland", "fi"],
    ["lf",   "Europe/France", "fr"],
    ["ed",   "Europe/Germany", "de"],
    ["lggg", "Europe/Greece", "gr"],
    ["lhcc", "Europe/Hungary", "hu"],
    ["li",   "Europe/Italy", "it"],
    ["ehaa", "Europe/Netherlands", "nl"],
    ["epww", "Europe/Poland", "pl"],
    ["lrbb", "Europe/Romania", "ro"],
    ["lzbb", "Europe/Slovakia", "sk"],
    ["ljla", "Europe/Slowenia", "si"],
    ["esaa", "Europe/Sweden", "se"],
    #
    # Europe - other
    #
    ["lsas", "Europe/Switzerland", "ch"],
]


def readAirspace(aseNode, shapeRoot, cat, nam, numCoordDigits):
    """Generate GeoJSON for airspace

    This method reads information about a given airspace from aseNode, finds
    the approriate geometry in the shape file and generates a GeoJSON feature.
    This is a generic method that is used by the more specialized methods
    readFeature_*.

    :param aseNode: An ElementTree xml node pointing to an airspace 'Ase' node

    :param shapeRoot: Root of the xml shape file

    :param cat: Category of the airspace, for inclusion in the GeoJSON 'CAT'
        field

    :param nam: Name of the airspace, for inclusion in the GeoJSON 'NAM' field.

    :param numCoordDigits: Numer of digits for coordinate pairs

    :returns: A feature dictionary, ready for inclusion in GeoJSON

    """

    aseUid = aseNode.find('AseUid')
    mid = aseUid.get('mid')

    # Get geometry
    coordinates = []
    gmlPosList = shapeRoot.find("./Ase/AseUid[@mid='{}']/../gmlPosList".format(mid)).text
    for coordinateTripleString in gmlPosList.split():
        coordinateTriple = coordinateTripleString.split(",")
        coordinate = [round(float(coordinateTriple[0]), numCoordDigits), round(float(coordinateTriple[1]), numCoordDigits)]
        coordinates.append(coordinate)
    # Make sure the polygon closes
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])

    # Get properties
    properties = {}
    properties['BOT'] = readHeight(aseNode, 'Lower', short=True)
    properties['CAT'] = cat
    properties['ID'] = mid
    properties['NAM'] = nam
    properties['MLI'] = nam
    properties['MLM'] = nam
    properties['TOP'] = readHeight(aseNode, 'Upper', short=True)
    properties['TYP'] = "AS"

    # Generate feature
    feature = {'type': 'Feature'}
    feature['geometry'] = {'type': 'Polygon', 'coordinates': [coordinates]}
    feature['properties'] = properties
    return feature


def readCoordinate(xmlNode, numCoordDigits):
    """Read coordinate from children of the given XML Node

    Takes an XML node, looks for children with name 'geoLat' and 'geoLong',
    reads and interprets coordinates, rounds them to the number of decimal
    places and returns an array with latitude and longitude as floats

    In case of error, this method will fail siliently and return undefined
    results.

    :param xmlNode: An ElementTree xml node

    :returns: A float with two elements, containing latitude and longitude
        as floats.

    """

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


def readFeatures_FISSectors(root, shapeRoot, numCoordDigits):
    """Generate GeoJSON for airspaces: Flight Information Sectors

    This method reads information about FIS-airspaces from an OFMX file, finds
    the approriate geometries in the shape file and generates GeoJSON features.

    :param root: Root of the OFMX file

    :param shapeRoot: Root of the OFMX shape file

    :param numCoordDigits: Numer of digits for coordinate pairs

    :returns: An array of feature dictionaries, ready for inclusion in GeoJSON

    """

    print("… FIS Sectors")
    FISfeatures = []
    for Ase in root.findall("./Ase/AseUid[codeType='SECTOR']/.."):
        AseUid = Ase.find('AseUid')
        AseMid = AseUid.get('mid')
        codeId = AseUid.find('codeId').text

        # Get service in airspace (SAE)
        Sae = root.find("./Sae/SaeUid/AseUid[@mid='{}']/../..".format(AseMid))
        if Sae == None:
            continue
        UniMid = Sae.find('SaeUid').find('SerUid').find('UniUid').get('mid')

        # Get frequency
        label = ""
        Fqy = root.find("./Fqy/FqyUid/SerUid/UniUid[@mid='{}']/../../..".format(UniMid))
        if Fqy == None:
            print("WARNING: No Frequency found for Ase {}, Uni {}".format(codeId, UniMid))
            label = codeId
        else:
            callSign  = Fqy.find('Cdl').find('txtCallSign').text
            frequency = Fqy.find('FqyUid').find('valFreqTrans').text + " " + Fqy.find('uomFreq').text
            label = callSign + " " + frequency

        FISfeature = readAirspace(Ase, shapeRoot, 'FIS', label, numCoordDigits)
        FISfeatures.append(FISfeature)
    return FISfeatures


def readFeatures_NRA(root, shapeRoot, numCoordDigits):
    """Generate GeoJSON for airspaces: Nature Reserve Areas

    This method reads information about NRA-airspaces from an OFMX file, finds
    the approriate geometries in the shape file and generates GeoJSON features.

    :param root: Root of the OFMX file

    :param shapeRoot: Root of the OFMX shape file

    :param numCoordDigits: Numer of digits for coordinate pairs

    :returns: An array of feature dictionaries, ready for inclusion in GeoJSON

    """

    print("… Nature Reserve Areas")
    NRAfeatures = []
    for nra in root.findall("./Ase/AseUid[codeType='NRA']/.."):
        NRAfeature = readAirspace(nra, shapeRoot, 'NRA', nra.find('txtName').text, numCoordDigits)
        NRAfeatures.append(NRAfeature)
    return NRAfeatures


def readFeatures_RP(root, numCoordDigits):
    """Generate GeoJSON for airspaces: Reporting Points

    This method reads information about reporting points from an OFMX file,
    finds the approriate geometries in the shape file and generates GeoJSON
    features.

    :param root: Root of the OFMX file

    :param numCoordDigits: Numer of digits for coordinate pairs

    :returns: An array of feature dictionaries, ready for inclusion in GeoJSON

    """

    print("… Reporting Points")
    RPfeatures = []
    for Dpn in root.findall('./Dpn'):
        if not Dpn.find("codeType").text in ["VFR-ENR", "VFR-MRP", "VFR-RP"]:
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
        feature['geometry'] = {'type': 'Point', 'coordinates': readCoordinate(DpnUid, numCoordDigits)}

        #
        # Properties
        #
        properties = {'TYP': 'WP'}
        properties['MID'] = DpnUid.get('mid')
        if Dpn.find("codeType").text == "VFR-ENR":
            properties['CAT'] = 'RP'
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

        # Property: ICA - optional
        #
        # A string with the ICAO code of an associated airfield, such as "EDDE".

        if APcodeId != "":
            properties['ICA'] = APcodeId

        # Property: NAM - required
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
        RPfeatures.append(feature)
    return RPfeatures
    

    for nra in root.findall("./Ase/AseUid[codeType='NRA']/.."):
        NRAfeature = readAirspace(nra, shapeRoot, 'NRA', nra.find('txtName').text, numCoordDigits)
        NRAfeatures.append(NRAfeature)
    return NRAfeatures


def readFeatures_Procedures(root, numCoordDigits):
    """Generate GeoJSON for airspaces: Procedures

    This method reads information about procedures from an OFMX file, and
    generates GeoJSON features.

    :param root: Root of the OFMX file

    :param numCoordDigits: Numer of digits for coordinate pairs

    :returns: An array of feature dictionaries, ready for inclusion in GeoJSON

    """

    print("… Procedures")

    PRCfeatures = []
    for prc in root.findall('./Prc'):
        PrcUid = prc.find('PrcUid')
        if (prc.find('codeType').text != "TRAFFIC_CIRCUIT") and ("VFR" not in prc.find('codeType').text):
            continue;
        if prc.find('usageType') != None:
            if prc.find('usageType').text != "FIXED_WING":
                continue;

        # Feature dictionary, will be filled in here and included into JSON
        PRCfeature = {'type': 'Feature'}

        # Get geometry
        coordinates = []
        if prc.find('_beztrajectory') == None:
            continue;
        if prc.find('_beztrajectory').find('gmlPosList') == None:
            continue;
        for coordinatePair in prc.find('_beztrajectory').find('gmlPosList').text.split():
            x = coordinatePair.split(',')
            coordinates.append([round(float(x[0]), numCoordDigits), round(float(x[1]), numCoordDigits)])
        PRCfeature['geometry'] = {'type': 'LineString', 'coordinates': coordinates}

        # Get text name
        txtName = prc.find('txtName').text

        # Check if height information is available. The information is pretty
        # hidden in OFMX, and the data extraction method varies, depending on
        # whether this is a traffic circuit or a vfr arrival, departure or
        # transit route.
        if prc.find('codeType').text == "TRAFFIC_CIRCUIT":
            # Get height - if procedure is TFC
            heightString = readHeight(prc, 'Tfc')
            if heightString != "":
                if txtName != "":
                    txtName = txtName + " "
                txtName = txtName + heightString
        else:
            # Get height - if procedure is not TFC. In this case, the procedure
            # is subdivided into a number of legs, each with an entry and exit
            # location, and each location with a height band. This is WAY too
            # complicated for us. We show the height band only if all bands
            # for all locations of all legs agree. Otherwise, we show nothing.
            heightBands = set()
            for leg in prc.findall('Leg'):
                band = readMinMaxHeight(leg.find('entry'))
                heightBands.add(band)
                band = readMinMaxHeight(leg.find('exit'))
                heightBands.add(band)
            if (len(heightBands) == 1) and not "" in heightBands:
                if txtName != "":
                    txtName = txtName + " "
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

        PRCfeature['properties'] = properties

        # Feature is now complete. Add it to the 'features' array
        PRCfeatures.append(PRCfeature)
    return PRCfeatures


def readHeight(xmlNode, ending, short=False):
    """Read height information from XML Node and return as human-readable string

    In OFMX, height information for property X in an xmlNode is usually
    specified by three subnodes that are named as follows.

    - codeDistVerX: Type altitude information (flight level, above ground, above
      MSL)

    - uomDistVerX: Unit of measurement

    - valDistVerX: Numerical value

    This method looks for these subnodes and interprets their content. If all
    goes well, it returns a human-readable string such as "GND", "100 ft GND",
    "2300 ft" or "FL 95". If the data is not found or cannot be interpreted,
    this method fails silently and an empty string is returned.

    :param xmlNode: An ElementTree xml node

    :param ending: Name of the property. This is the string 'X' described above.

    :param short: If set to 'True', the method will create slightly shorter
        strings, of the form "GND", "100 AGL", "2300" or "FL 95"

    :returns: A string describing altitude, or an empty string in case of error

    """

    # Code - this is STD (=flight level), HEI (=height over ground), ALT (=height over MSL)
    if xmlNode.find('codeDistVer'+ending) == None:
        return "";
    codeDistVer = xmlNode.find('codeDistVer'+ending).text
    if codeDistVer == None:
        return "";
    if (codeDistVer != 'STD') and (codeDistVer != 'HEI') and (codeDistVer != 'ALT'):
        return ""

    # Read units of measurement - this is FL (=flight level), FT (=feet), M (=meters)
    if xmlNode.find('uomDistVer'+ending) == None:
        return "";
    uomDistVer = xmlNode.find('uomDistVer'+ending).text
    if uomDistVer == None:
        return "";
    if (uomDistVer != 'FL') and (uomDistVer != 'FT') and (uomDistVer != 'M'):
        print("WARNING: Error in readOFMXHeight uomDistVer is " + uomDistVer)
        return ""

    # Read value -- this is meant to be a number
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
        print("WARNING: Cannot interpret number '{}' in {}".format(valDistVer, xmlNode.find('PrcUid').attrib))

    # Compile final result string
    if uomDistVer == 'FL':
        return "FL " + valDistVer
    if codeDistVer == "HEI":
        if valDistVer == "0":
            return "GND"
        if short:
            return valDistVer + " AGL"
        return valDistVer + " " + uomDistVer.lower() + " AGL"
    if codeDistVer == "ALT":
        if short:
            return valDistVer
        return valDistVer + " " + uomDistVer.lower()

    return ""


def readMinMaxHeight(xmlNode):
    """Read height information - height bands

    In OFMX, height bands for VFR procedure for X in usually specified by six
    subnodes, called "codeDistVerLower", "uomDistVerLower", "valDistVerLower",
    "codeDistVerUpper", "uomDistVerUpper" and "valDistVerUpper". This method
    looks for these subnodes and interprets their content. If all goes well, it
    returns a string such as "MIN. 100 ft GND", "MIN. 2500 ft · MAX 4500 ft
    MSL". If the data is not found or cannot be interpreted, an empty string is
    returned.

    :param xmlNode: An ElementTree xml node

    :returns: A string describing minimal and maximal altitude, or an empty
        string in case of error

    """

    lower = readHeight(xmlNode, 'Lower')
    upper = readHeight(xmlNode, 'Upper')
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


def downloadXML(filename):
    try:
        response = requests.get(filename)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("Error downloading " + filename)
        print(errh)
        exit(-1)
    except requests.exceptions.ConnectionError as errc:
        print("Error downloading " + filename)
        print(errc)
        exit(-1)
    except requests.exceptions.Timeout as errt:
        print("Error downloading " + filename)
        print(errt)
        exit(-1)
    except requests.exceptions.RequestException as err:
        print("Error downloading " + filename)
        print(err)
        exit(-1)

    try:
        response.encoding = 'utf-8'
        result = ET.fromstring(response.text)
    except Exception as err:
        print("Succesfully downloaded " + filename)
        print("Error parsing XML")
        print(err)
        exit(-1)
    return result


def readOFMX():
    #
    # Compute current airac cycle
    #
    airac_number = 1
    airac_year   = 2020
    airac_date   = datetime.date.fromisoformat('2020-01-02')
    airac_delta  = datetime.timedelta(days=28)

    while airac_date+airac_delta < datetime.date.today():
        airac_date += airac_delta

        if airac_date.year > airac_year:
            airac_year = airac_date.year
            airac_number = 1
        else:
            airac_number += 1
    airac = "{:02}{:02}".format(airac_year%100, airac_number)
    airac = "2511"  # TEMPORARY FIX TO AVOID 404 ERRORS DUE TO MISSING FILES
    print("OFM: Current AIRAC cycle is {}\n".format(airac))

    features = []
    for region in regions:
        print("OFM: Working on region " + region[1])
        root = downloadXML("https://storage.googleapis.com/snapshots.openflightmaps.org/live/{0}/ofmx/{1}/latest/embedded/ofmx_{2}.xml".format(airac, region[0], region[0][0:2]))
        shapeRoot = downloadXML("https://storage.googleapis.com/snapshots.openflightmaps.org/live/{0}/ofmx/{1}/latest/embedded/ofmx_{2}_ofmShapeExtension.xml".format(airac, region[0], region[0][0:2]))

        #features += readFeatures_FISSectors(root, shapeRoot, 5)
        features += readFeatures_NRA(root, shapeRoot, 5)
        features += readFeatures_Procedures(root, 5)
        features += readFeatures_RP(root, 5)
    return features
