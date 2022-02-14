#!/bin/python3

import datetime
import filecmp
import glob
import json
import os
import shutil
import subprocess


stagingDir = "../staging"
serverURL = 'https://cplx.vm.uni-freiburg.de/storage/enroute-GeoJSONv003'
whatsNewText = 'If you ever move to the south Atlantic, you will be delighted to learn that aviation maps for the <strong>Falkland Islands</strong> are now available.'

#
# Copy files over to the mapStorageDir
#
os.chdir('out')
for fileName in glob.glob("**/*.geojson", recursive=True)+glob.glob("**/*.mbtiles", recursive=True)+glob.glob("**/*.txt", recursive=True):
    stagingFileName = stagingDir+'/'+fileName
    hasChanged = True
    
    #
    # Check if files really did change
    #
    if fileName.endswith('geojson'):
        A = json.load( open(fileName) )
        A['info'] = 'infoString'
        B = json.load( open(stagingFileName) )
        B['info'] = 'infoString'
        if A == B:
            hasChanged = False

    if fileName.endswith('txt'):
        A = open(fileName).readlines()[1:]
        B = open(stagingFileName).readlines()[1:]
        if A == B:
            hasChanged = False

    if fileName.endswith('mbtiles'):
        if filecmp.cmp(fileName, stagingFileName, shallow=False):
            hasChanged = False

    if hasChanged:
        print('\033[1mZopfli compress {} and move to staging dir\033[0m'.format(fileName))
        subprocess.run("rm -f '" + fileName + ".gz'", shell=True, check=True)
        subprocess.run("zopfli --best '" + fileName + "'", shell=True, check=True)
        shutil.move(fileName, stagingFileName)
        shutil.move(fileName+'.gz', stagingFileName+'.gz')
    else:
        print('Skipping over {}, which is unchanged'.format(fileName))
        os.remove(fileName)


#
# Generate maps.json
#
print("\nGenerate maps.json")
maps = []
for fileName in glob.glob(stagingDir + "/**/*.geojson", recursive=True)+glob.glob(stagingDir + "/**/*.mbtiles", recursive=True)+glob.glob(stagingDir + "/**/*.txt", recursive=True):
    map = {}
    map['path']  = fileName.replace(stagingDir + "/", "")
    t = os.path.getmtime(fileName)
    d = datetime.datetime.fromtimestamp(t)
    map['time'] = ("%04d" % d.year) + ("%02d" % d.month) + ("%02d" % d.day)
    map['size'] = os.path.getsize(fileName)
    maps.append(map)

top = {'maps': maps}
top['url'] = serverURL
top['whatsNew'] = whatsNewText
fileName = open(stagingDir + '/maps.json', 'w')
fileName.write(json.dumps(top, sort_keys=True, indent=4))
fileName.close()

key = input("Upload maps (y/n)? ")
if key == "y":
    subprocess.run(
        "rsync -e ssh -vaz --delete "
        + stagingDir
        + "/ kebekus@cplx.vm.uni-freiburg.de:/var/www/storage/enroute-GeoJSONv003",
        shell=True,
        check=True,
    )
