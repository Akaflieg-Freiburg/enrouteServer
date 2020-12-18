"""
OFMX
====================================
Tools to interpret ofmx files
"""


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
