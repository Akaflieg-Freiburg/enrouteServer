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
            "aixm.zip",
        )
        print("  … extracting")
        with zipfile.ZipFile("aixm.zip", "r") as zip_ref:
            fileName = "aixm_" + region[0][0:2] + "/isolated/aixm_" + region[0][0:2] + ".xml"
            zip_ref.extract(fileName)
            os.rename(fileName, "aixm.xml")
            # Delete leftover files
            os.remove("aixm.zip")
            shutil.rmtree("aixm_" + region[0][0:2])

    print("  … downloading openAIP asp")
    urlText = "http://www.openaip.net/customer_export_asdkjb1iufbiqbciggb34ogg/" + region[2] + "_asp.aip"
    urllib.request.urlretrieve( urlText, "asp.aip" )
    print("  … downloading openAIP nav")
    urlText = "http://www.openaip.net/customer_export_asdkjb1iufbiqbciggb34ogg/" + region[2] + "_nav.aip"
    urllib.request.urlretrieve( urlText, "nav.aip" )
    print("  … downloading openAIP wpt")
    urlText = "http://www.openaip.net/customer_export_asdkjb1iufbiqbciggb34ogg/" + region[2] + "_wpt.aip"
    urllib.request.urlretrieve( urlText, "wpt.aip" )

    print("  … generate GeoJSON")
    if region[0] != "":
        subprocess.run(
            "any2GeoJSON.py asp.aip nav.aip wpt.aip aixm.xml",
            shell=True,
            check=True,
        )
    else:
        subprocess.run(
            "any2GeoJSON.py asp.aip nav.aip wpt.aip",
            shell=True,
            check=True,
        )
    os.makedirs(mapStorageDir + "/" + region[1].split('/')[0], exist_ok=True)
    outputFile = mapStorageDir + "/" + region[1] + ".geojson"
    # WARNING! Fails if file does not already exist
    if os.path.isfile(outputFile) and filecmp.cmp(
        "test.geojson", outputFile, shallow=False
    ):
        print("GeoJSON file has not changed. Keeping old version.")
    else:
        print("GeoJSON file has changed. Taking new version.")
        os.rename("test.geojson", outputFile)
    print("\n")


print("Generate maps.json")
maps = []
for file in glob.glob(mapStorageDir + "/**/*.geojson", recursive=True)+glob.glob(mapStorageDir + "/**/*.mbtiles", recursive=True):
    map = {}
    map['path']  = file.replace(mapStorageDir + "/", "")
    t = os.path.getmtime(file)
    d = datetime.datetime.fromtimestamp(t)
    map['time'] = ("%04d" % d.year) + ("%02d" % d.month) + ("%02d" % d.day)
    map['size'] = os.path.getsize(file)
    maps.append(map)

top = {'maps': maps}
top['url'] = serverURL
file = open(mapStorageDir + '/maps.json', 'w')
file.write(json.dumps(top, sort_keys=True, indent=4))
file.close()

key = input("Upload maps (y/n)? ")
if key == "y":
    subprocess.run(
        "rsync -e ssh -vaz --delete "
        + mapStorageDir
        + "/ kebekus@cplx.vm.uni-freiburg.de:/var/www/storage/enroute-GeoJSONv001",
        shell=True,
        check=True,
    )
