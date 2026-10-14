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
    ["ljla", "Europe/Slovenia", "si"],
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


def readBezierTrajectory(xmlNode, numCoordDigits, samplesPerCurve=10):
    """Read a Bézier trajectory from an OFMX node and return a polyline

    OFMX procedures carry their rounded geometry in a node '_beztrajectory',
    whose child 'gmlPosList' contains a chain of cubic Bézier curves, encoded
    in the style of an SVG path: the first point is the start anchor, and every
    following group of three points consists of two control points and the
    next anchor. Straight stretches are encoded as degenerate curves whose
    control points are collinear with the anchors.

    This method decodes the chain into a polyline. Straight segments are
    emitted as a single vertex, curved segments are sampled at a fixed number
    of parameter values, so that the rounded corners of traffic circuits
    survive the conversion to GeoJSON.

    :param xmlNode: An ElementTree xml node with a child 'gmlPosList'

    :param numCoordDigits: Number of digits for coordinate pairs

    :param samplesPerCurve: Number of vertices generated for each curved
        segment

    :returns: An array of coordinate pairs [longitude, latitude], or an empty
        array if the node does not contain a valid Bézier chain.

    """

    posList = xmlNode.find('gmlPosList')
    if posList is None or not posList.text:
        return []

    points = []
    for coordinatePair in posList.text.split():
        x = coordinatePair.split(',')
        points.append((float(x[0]), float(x[1])))
    if (len(points) < 2) or ((len(points)-1) % 3 != 0):
        print("WARNING: Bézier trajectory with {} points cannot be interpreted".format(len(points)))
        return []

    def isStraight(p0, p1, p2, p3):
        # A segment is considered straight if both control points lie on the
        # line through the anchors, up to a tolerance of 1e-6 degrees (about
        # 10cm). If the anchors coincide, the control points must coincide
        # with them as well.
        dx = p3[0]-p0[0]
        dy = p3[1]-p0[1]
        length = (dx*dx+dy*dy)**0.5
        for p in (p1, p2):
            if length < 1e-9:
                dist = ((p[0]-p0[0])**2+(p[1]-p0[1])**2)**0.5
            else:
                dist = abs(dx*(p[1]-p0[1])-dy*(p[0]-p0[0]))/length
            if dist > 1e-6:
                return False
        return True

    coordinates = []
    def append(p):
        rounded = [round(p[0], numCoordDigits), round(p[1], numCoordDigits)]
        if (len(coordinates) == 0) or (coordinates[-1] != rounded):
            coordinates.append(rounded)

    append(points[0])
    for i in range(0, len(points)-1, 3):
        p0, p1, p2, p3 = points[i:i+4]
        if isStraight(p0, p1, p2, p3):
            append(p3)
            continue
        for k in range(1, samplesPerCurve+1):
            t = k/samplesPerCurve
            u = 1.0-t
            append((u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
                    u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]))
    return coordinates


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

        # Get geometry. The trajectory is a chain of cubic Bézier curves,
        # which we convert into a polyline with rounded corners.
        if prc.find('_beztrajectory') == None:
            continue;
        coordinates = readBezierTrajectory(prc.find('_beztrajectory'), numCoordDigits)
        if len(coordinates) < 2:
            continue;
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


def currentAirac(today=None):
    """
    Compute the AIRAC cycle identifier that is current on a given day.

    :param today: Date for which the AIRAC cycle is computed. Defaults to
        today's date.

    :returns: The four-digit AIRAC identifier as a string, e.g. "2610".
        This is the identifier used in the download URLs of the open
        flightmaps snapshot server.
    """
    if today is None:
        today = datetime.date.today()

    airac_number = 1
    airac_year   = 2020
    airac_date   = datetime.date.fromisoformat('2020-01-02')
    airac_delta  = datetime.timedelta(days=28)

    while airac_date+airac_delta < today:
        airac_date += airac_delta

        if airac_date.year > airac_year:
            airac_year = airac_date.year
            airac_number = 1
        else:
            airac_number += 1
    return "{:02}{:02}".format(airac_year%100, airac_number)


def readOFMX():
    airac = currentAirac()
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
