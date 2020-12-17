"""
OFMX
====================================
Tools to interpret ofmx files
"""


def readHeight4GeoJSON(xmlNode, ending):
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
        print("Error in OFMX.readOFMXHeight codeDistVer is " + codeDistVer)
        exit(-1)

    # Read units of measurement - this is FL (=flight level), FT (=feet), M (=meters)
    if xmlNode.find('uomDistVer'+ending) == None:
        return "";
    uomDistVer = xmlNode.find('uomDistVer'+ending).text
    if uomDistVer == None:
        return "";
    if (uomDistVer != 'FL') and (uomDistVer != 'FT') and (uomDistVer != 'M'):
        print("Error in OFMX.readOFMXHeight uomDistVer is " + uomDistVer)
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


def readHeight(xmlNode, ending):
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

    :returns: A string such as "GND", "100 FT GND", "2300 FT MSL" or "FL 95", or an empty string in case of error

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
