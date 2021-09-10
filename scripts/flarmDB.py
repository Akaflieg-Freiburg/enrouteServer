#!/bin/python

"""
flarmDB
====================================
Tools to compactify a Flarmnet database downloaded from
https://www.flarmnet.org/static/files/wfn/data.fln
"""

import re


def readFlarmDB(inFileName, outFileName):
    """Read a Flarmnet database in fln format (as also used by LXNavigation/XCSoar, WinPilot, LK8000, ClearNav)
    and generate an output file with compactified data, containing a dicitionary Flarm ID => aircraft registraton.
    Input data where the 'registration' field is not obviously a well-defined registration are ignored.

    The output file is a plain text file in ISO-8859-1 encoding ("Latin1"). The first line is a short description
    of the content. Every following line is exactly 24 bytes long. 
    
    - Bytes  0 -  5 of the line contain the Flarm ID
    - Bytes  7 - 22 of the line contain the registration, left justified and filled with space

    The lines in the output file are sorted alphabetically by Flarm ID.

    This function will raise an exception on error

    :param inFileName: Name of input file

    :param outFileName: Name of output file

    """

    # Regular expression to check if a registration is valid
    validReg = re.compile('^([A-Z0-9]{1,2}-[A-Z0-9]*|N[A-Z0-9]{2,6})$')

    FLARMfile = open(inFileName, 'r')
    version = FLARMfile.readline()

    outfile = open(outFileName, 'w', encoding='ISO-8859-1')
    outfile.write("Flarmnet Data version "+version)

    for line in FLARMfile.readlines():
        ascii = bytearray.fromhex(line).decode("latin1")
        FLARMID = ascii[0:6]
        registration = ascii[27:48].strip()

        # Check if registration is meaningful
        if not validReg.match(registration):
            continue
        if registration == "":
            continue
        outfile.write(FLARMID)
        outfile.write(",")
        outfile.write(registration.ljust(16))
        outfile.write("\n")


readFlarmDB('/home/kebekus/Downloads/data.fln', 'flarmDB.txt')