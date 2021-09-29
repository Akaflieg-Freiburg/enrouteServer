#!/bin/python

"""
flarmDB
====================================
Tools to compactify a Flarmnet database downloaded from
https://www.flarmnet.org/static/files/wfn/data.fln
"""

import re


def readFlarmnetDB(inFileName, dictionary):
    """Read a Flarmnet database in fln format (as also used by
    LXNavigation/XCSoar, WinPilot, LK8000, ClearNav).  Files of this form can be
    downloaded from Flarmnet, at this url:
    https://www.flarmnet.org/static/files/wfn/data.fln The method fills a
    dicitionary that maps Flarm IDs to aircraft callsigns. Input data where the
    'callsign' field is not obviously a well-defined callsign are ignored. This
    function will raise an exception on error

    :param inFileName: Name of input file

    :param dictionary: Dictionary to which the results will be appended

    :returns: String that describes the input file version

    """

    # Regular expression to check if a callsign is valid
    validReg = re.compile('^([A-Z0-9]{1,2}-[A-Z0-9]*|N[A-Z0-9]{2,6})$')

    FLARMfile = open(inFileName, 'r')
    version = FLARMfile.readline()

    for line in FLARMfile.readlines():
        ascii = bytearray.fromhex(line).decode("latin1")
        FlarmID  = ascii[0:6].upper()
        callsign = ascii[27:48].strip().upper()

        # Check if registration is meaningful
        if not validReg.match(callsign):
            continue
        if callsign == "":
            continue
        if not FlarmID in dictionary:
            dictionary[FlarmID] = callsign
    return "Flarmnet Data version "+version


def readFlarmDB(inFileName, outFileName):
    """Read a Flarmnet database in fln format (as also used by
    LXNavigation/XCSoar, WinPilot, LK8000, ClearNav) and write a plain text file
    in ISO-8859-1 encoding ("Latin1"). The first line is a short description of
    the content. Every following line is exactly 24 bytes long.

    - Bytes  0 -  5 of the line contain the Flarm ID
    - Bytes  7 - 22 of the line contain the aircraft callsign, left justified
      and filled with space

    The lines in the output file are sorted alphabetically by Flarm ID.

    This function will raise an exception on error

    :param inFileName: Name of input file

    :param outFileName: Name of output file

    """

    result = {}

    version = readFlarmnetDB(inFileName, result)

    outfile = open(outFileName, 'w', encoding='ISO-8859-1')
    outfile.write(version)
    for FLARMID, callsign in result.items():
        outfile.write(FLARMID)
        outfile.write(",")
        outfile.write(callsign.ljust(16))
        outfile.write("\n")

readFlarmDB('/home/kebekus/Downloads/data.fln', 'flarmDB.txt')
