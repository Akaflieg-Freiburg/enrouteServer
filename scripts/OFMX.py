"""
OFMX
====================================
Tools to interpret ofmx files
"""

import re

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
    properties['TOP'] = readHeight(aseNode, 'Upper', short=True)
    properties['TYP'] = "AS"

    # Generate feature
    feature = {'type': 'Feature'}
    feature['geometry'] = {'type': 'Polygon', 'coordinates': [coordinates]}
    feature['properties'] = properties
    return feature


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
        SerMid = Sae.find('SaeUid').find('SerUid').get('mid')

        # Get frequency
        label = ""
        Fqy = root.find("./Fqy/FqyUid/SerUid[@mid='{}']/../..".format(SerMid))
        if Fqy == None:
            print("WARNING: No Frequency found for Ase {}, Sae {}".format(codeId, SerMid))
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
                band = readMinMaxHeight(leg.find('entry'))
                heightBands.add(band)
                band = readMinMaxHeight(leg.find('exit'))
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

        PRCfeature['properties'] = properties

        # Feature is now complete. Add it to the 'features' array
        PRCfeatures.append(PRCfeature)
    return PRCfeatures


def readHeight(xmlNode, ending, short=False):
    """Read height information from XML Node and return as human-readable string

    In OFMX, height information for property X in an xmlNode is usually
    specified by three subnodes that are named as follows.

    - codeDistVerX: Type altitude information (flight level, above ground, above MSL)

    - uomDistVerX: Unit of measurement

    - valDistVerX: Numerical value

    This method looks for these subnodes and interprets their content. If all
    goes well, it returns a human-readable string such as "GND", "100 FT GND",
    "2300 FT MSL" or "FL 95". If the data is not found or cannot be interpreted,
    this method fails silently and an empty string is returned.

    :param xmlNode: An ElementTree xml node

    :param ending: Name of the property. This is the string 'X' described above.

    :param short: If set to 'True', the method will create slightly shorter strings, of the form "GND", "100 AGL", "2300" or "FL 95"

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
        return valDistVer + " " + uomDistVer + " AGL"
    if codeDistVer == "ALT":
        if short:
            return valDistVer
        return valDistVer + " " + uomDistVer + " MSL"

    return ""


def readMinMaxHeight(xmlNode):
    """Read height information - height bands

    In OFMX, height bands for VFR procedure for X in usually specified by six
    subnodes, called "codeDistVerLower", "uomDistVerLower", "valDistVerLower",
    "codeDistVerUpper", "uomDistVerUpper" and "valDistVerUpper". This method
    looks for these subnodes and interprets their content. If all goes well, it
    returns a string such as "MIN. 100 FT GND", "MIN. 2500 FT MSL · MAX 4500 FT
    MSL". If the data is not found or cannot be interpreted, an empty string is
    returned.

    :param xmlNode: An ElementTree xml node

    :returns: A string describing minimal and maximal altitude, or an empty string in case of error

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
