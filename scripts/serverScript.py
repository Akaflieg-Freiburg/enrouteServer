#!/bin/python3

import datetime
import filecmp
import glob
import json
import os.path, time
import shutil
import subprocess
import urllib.request
import sys
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
    ["",     "Europe/Serbia", "rs"],
    ["lsas", "Europe/Switzerland", "ch"],
    ["",     "Europe/United Kingdom", "gb"],
    #
    # North America
    #
    ["",     "North America/Canada", "ca"],
    ["",     "North America/United States", "us"],
    #
    # South America
    #
    ["",     "South America/Argentina", "ar"],
    ["",     "South America/Brazil", "br"],
]


workingDir = "/home/kebekus/experiment/enroute_working"
mapStorageDir = "/home/kebekus/Austausch/aviation_maps"
serverURL = "https://cplx.vm.uni-freiburg.de/storage/enroute-GeoJSONv001"

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
print("Info: Current AIRAC cycle is {}\n".format(airac))


opener = urllib.request.build_opener()
opener.addheaders = [("User-agent", "Mozilla/5.0")]
urllib.request.install_opener(opener)

shutil.rmtree(workingDir, ignore_errors=True)
os.makedirs(workingDir, exist_ok=True)
os.chdir(workingDir)

for region in regions:
    print("Working on region " + region[1])

    if region[0] != "":
        # Download and extract OFMX
        print("  … downloading OFMX")
        urllib.request.urlretrieve(
            "https://storage.googleapis.com/snapshots.openflightmaps.org/live/{0}/ofmx/{1}/latest/isolated/ofmx_{2}.xml".format(airac, region[0], region[0][0:2]),
            "data.ofmx"
        )

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
            "{0}/any2GeoJSON.py {1}/asp.aip {1}/nav.aip {1}/wpt.aip {1}/data.ofmx ".format(sys.path[0], workingDir),
            shell=True,
            check=True,
        )
    else:
        subprocess.run(
            "{0}/any2GeoJSON.py {1}/asp.aip {1}/nav.aip {1}/wpt.aip".format(sys.path[0], workingDir),
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
        print("GeoJSON file has changed. Taking new version, generating Zopfli compressed version.")
        os.rename("test.geojson", outputFile)
        subprocess.run("rm -f '"+outputFile+".gz'", shell=True, check=True)
        subprocess.run("zopfli --best '"+outputFile+"'", shell=True, check=True)
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
        + "/ kebekus@cplx.vm.uni-freiburg.de:/var/www/storage/enroute-GeoJSONv002",
        shell=True,
        check=True,
    )
