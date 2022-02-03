#!/bin/python3

import datetime
import glob
import json
import os
import shutil
import subprocess


mapStorageDir = "/home/kebekus/Austausch/aviation_maps"
serverURL = "https://cplx.vm.uni-freiburg.de/storage/enroute-GeoJSONv002"

#
# Copy files over to the mapStorageDir
#
os.chdir('out')
for file in glob.glob("**/*.geojson", recursive=True)+glob.glob("**/*.mbtiles", recursive=True)+glob.glob("**/*.txt", recursive=True):
    print('Zopfli compress {}'.format(file))
    subprocess.run("rm -f '" + file + ".gz'", shell=True, check=True)
    subprocess.run("zopfli --best '" + file + "'", shell=True, check=True)
    shutil.move(file, mapStorageDir+'/'+file)
    shutil.move(file+'.gz', mapStorageDir+'/'+file+'.gz')


#
# Generate maps.json
#
print("\nGenerate maps.json")
maps = []
for file in glob.glob(mapStorageDir + "/**/*.geojson", recursive=True)+glob.glob(mapStorageDir + "/**/*.mbtiles", recursive=True)+glob.glob(mapStorageDir + "/**/*.txt", recursive=True):
    map = {}
    map['path']  = file.replace(mapStorageDir + "/", "")
    t = os.path.getmtime(file)
    d = datetime.datetime.fromtimestamp(t)
    map['time'] = ("%04d" % d.year) + ("%02d" % d.month) + ("%02d" % d.day)
    map['size'] = os.path.getsize(file)
    maps.append(map)

top = {'maps': maps}
top['url'] = serverURL
top['whatsNew'] = 'If you ever move to the south Atlantic, you will be delighted to learn that aviation maps for the <strong>Falkland Islands</strong> are now available.'
file = open(mapStorageDir + '/maps.json', 'w')
file.write(json.dumps(top, sort_keys=True, indent=4))
file.close()

key = input("Upload maps (y/n)? ")
if key == "y":
    subprocess.run(
        "rsync -e ssh -vaz --delete "
        + mapStorageDir
        + "/ kebekus@cplx.vm.uni-freiburg.de:/var/www/storage/enroute-GeoJSONv003",
        shell=True,
        check=True,
    )
