#!/bin/python3

import datetime
import filecmp
import geopandas
import glob
import json
import os
import shutil
import subprocess


mapStorageDir = "/home/kebekus/Austausch/aviation_maps"
serverURL = "https://cplx.vm.uni-freiburg.de/storage/enroute-GeoJSONv003"

#
# Copy files over to the mapStorageDir
#
os.chdir('out')
for fileName in glob.glob("**/*.geojson", recursive=True)+glob.glob("**/*.mbtiles", recursive=True)+glob.glob("**/*.txt", recursive=True):
    stagingFileName = mapStorageDir+'/'+fileName
    hasChanged = True
#    if filecmp.cmp(file, mapStorageDir+'/'+file, shallow=False):
#        hasChanged = False
    
    if (fileName.endswith('geojson')):
        A = json.load( open(fileName) )
        A['info'] = 'infoString'
        B = json.load( open(stagingFileName) )
        B['info'] = 'infoString'
        if A == B:
            hasChanged = False

    if hasChanged:
        print('Zopfli compress {} and move to staging dir'.format(fileName))
        subprocess.run("rm -f '" + fileName + ".gz'", shell=True, check=True)
        subprocess.run("zopfli --best '" + fileName + "'", shell=True, check=True)
        shutil.move(fileName, stagingFileName)
        shutil.move(fileName+'.gz', stagingFileName+'.gz')
    else:
        print('Skipping over {}, which is unchanged'.format(fileName))


#
# Generate maps.json
#
print("\nGenerate maps.json")
maps = []
for fileName in glob.glob(mapStorageDir + "/**/*.geojson", recursive=True)+glob.glob(mapStorageDir + "/**/*.mbtiles", recursive=True)+glob.glob(mapStorageDir + "/**/*.txt", recursive=True):
    map = {}
    map['path']  = fileName.replace(mapStorageDir + "/", "")
    t = os.path.getmtime(fileName)
    d = datetime.datetime.fromtimestamp(t)
    map['time'] = ("%04d" % d.year) + ("%02d" % d.month) + ("%02d" % d.day)
    map['size'] = os.path.getsize(fileName)
    maps.append(map)

top = {'maps': maps}
top['url'] = serverURL
top['whatsNew'] = 'If you ever move to the south Atlantic, you will be delighted to learn that aviation maps for the <strong>Falkland Islands</strong> are now available.'
fileName = open(mapStorageDir + '/maps.json', 'w')
fileName.write(json.dumps(top, sort_keys=True, indent=4))
fileName.close()

key = input("Upload maps (y/n)? ")
if key == "y":
    subprocess.run(
        "rsync -e ssh -vaz --delete "
        + mapStorageDir
        + "/ kebekus@cplx.vm.uni-freiburg.de:/var/www/storage/enroute-GeoJSONv003",
        shell=True,
        check=True,
    )
