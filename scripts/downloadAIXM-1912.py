#!/bin/python3

import datetime
import filecmp
import glob
import json
import os.path, time
import shutil
import subprocess
import urllib.request
import zipfile

regions = [
    #
    # Africa
    #
    ["fa",   "Africa/South Africa", "za"],
    ["fywh", "Africa/Namibia", "na"],
    #
    # Australia Oceanica
    #
    ["",     "Australia Oceanica/Australia", "au"],
    ["",     "Australia Oceanica/New Zealand", "nz"],
    #
    # Europe - EU27
    #
    ["lovv", "Europe/Austria", "at"],
    ["ebbu", "Europe/Belgium", "be"],
    ["lbsr", "Europe/Bulgaria", "bg"],
    ["ldzo", "Europe/Croatia", "hr"],
    ["",     "Europe/Cyprus", "cy"],
    ["lkaa", "Europe/Czech Republic", "cz"],
    ["ekdk", "Europe/Denmark", "dk"],
    ["",     "Europe/Estonia", "ee"],
    ["efin", "Europe/Finland", "fi"],
    ["",     "Europe/France", "fr"],
    ["ed",   "Europe/Germany", "de"],
    ["lggg", "Europe/Greece", "gr"],
    ["lhcc", "Europe/Hungary", "hu"],
    ["",     "Europe/Ireland", "ie"],
    ["li",   "Europe/Italy", "it"],
    ["",     "Europe/Latvia", "lv"],
    ["",     "Europe/Lithuania", "lt"],
    ["",     "Europe/Luxembourg", "lu"],
    ["",     "Europe/Malta", "mt"],
    ["ehaa", "Europe/Netherlands", "nl"],
    ["epww", "Europe/Poland", "pl"],
    ["",     "Europe/Portugal", "pt"],
    ["lrbb", "Europe/Romania", "ro"],
    ["lzbb", "Europe/Slovakia", "sk"],
    ["ljla", "Europe/Slowenia", "si"],
    ["",     "Europe/Spain", "es"],
    ["esaa", "Europe/Sweden", "se"],
    #
    # Europe - other
    #
    ["",     "Europe/Iceland", "is"],
    ["",     "Europe/Liechtenstein", "li"],
    ["",     "Europe/Norway", "no"],
    ["lsas", "Europe/Switzerland", "ch"],
    ["",     "Europe/United Kingdom", "gb"],
    #
    # North America
    #
    ["",     "North America/Canada", "ca"],
    ["",     "North America/United States", "us"],
]


workingDir = "/home/kebekus/experiment/enroute_working"
mapStorageDir = "/home/kebekus/Austausch/aviation_maps"
serverURL = "https://cplx.vm.uni-freiburg.de/storage/enroute-GeoJSONv001"
airac = ("%04d" % datetime.date.today().year)[2:4] + (
    "%02d" % datetime.date.today().month
)
airac = "1912"

opener = urllib.request.build_opener()
opener.addheaders = [("User-agent", "Mozilla/5.0")]
urllib.request.install_opener(opener)

shutil.rmtree(workingDir, ignore_errors=True)
os.makedirs(workingDir, exist_ok=True)
os.chdir(workingDir)

for region in regions:
    print("Working on region " + region[1])

    if region[0] != "":
        print("  … downloading AIXM")
        urllib.request.urlretrieve(
            "http://snapshots.openflightmaps.org/live/"
            + airac
            + "/aixm45/"
            + region[0]
            + "/latest/aixm_"
            + region[0][0:2]
            + ".zip",
            "aixm_" + region[0][0:2] + ".zip",
        )
