import datetime
import filecmp
import glob
import json
import os
import regions
import shutil
import subprocess
import sys


stagingDir = "../staging"
serverURL = 'https://enroute-data.akaflieg-freiburg.de/enroute-GeoJSONv003'
whatsNewText = 'Enroute Flight Navigation now offers the official ICAO 500k raster map for France. Open the main menu and go to "Library/Maps and Data" to download it. We thank the french Service de l’Information Aéronautique for providing the data, and Quentin Bossard for making the map available in Enroute.'
minAppVersion = '2.31.8'

# Go to output directory
os.chdir('out')

#
# Sync the staging dir with the server
#
print('Sync the staging dir with the server')
subprocess.run(
    "rsync -e 'ssh -p222' -vaz --delete "
    + "akafli@www595.your-server.de:public_html/enroute-data/enroute-GeoJSONv003/ " 
    + stagingDir,
    shell=True,
    check=True
)


#
# Pass 1: sanity-check all files and determine which ones have changed. No file
# is touched in this pass, so a sanity-check failure leaves the staging dir in
# a consistent state and reports all offending files at once.
#
maxGeojsonSize = 40*1024*1024
offenders = []
filesToProcess = []
for fileName in glob.glob("**/*.geojson", recursive=True)+glob.glob("**/*.mbtiles", recursive=True)+glob.glob("**/*.terrain", recursive=True)+glob.glob("**/*.raster", recursive=True)+glob.glob("**/*.vac", recursive=True)+glob.glob("**/*.txt", recursive=True):
    stagingFileName = stagingDir+'/'+fileName
    hasChanged = True
    Asize = os.path.getsize(fileName)

    #
    # Aviation GeoJSON files beyond all reasonable size overwhelm the app on
    # mobile devices (see enroute issue #676). Refuse to deploy them, even if
    # there is no previously deployed version to compare against.
    #
    if fileName.endswith('geojson') and (Asize > maxGeojsonSize):
        offenders.append('{} is {:.1f} MiB, exceeding the limit of {:.0f} MiB'.format(fileName, Asize/(1024*1024), maxGeojsonSize/(1024*1024)))

    if os.path.exists(stagingFileName):
        #
        # If file sizes changes by more than 10%, then probably something is
        # wrong. In that case, exit with an error.
        #
        Bsize = os.path.getsize(stagingFileName)
        if (Asize < 0.9*Bsize) or (0.9*Asize > Bsize):
            offenders.append('{} has changed size by more than 10% ({:.1f} MiB -> {:.1f} MiB)'.format(fileName, Bsize/(1024*1024), Asize/(1024*1024)))

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

        if fileName.endswith('mbtiles') or fileName.endswith('terrain') or fileName.endswith('raster') or fileName.endswith('vac'):
            if filecmp.cmp(fileName, stagingFileName, shallow=False):
                hasChanged = False

    filesToProcess.append((fileName, stagingFileName, hasChanged))

if offenders:
    print('\nSanity check found {} suspicious file(s):'.format(len(offenders)))
    for offender in offenders:
        print('  ' + offender)
    if "force" not in sys.argv:
        print('Human intervention is required.')
        exit(-1)
    print('Proceeding anyway, because "force" was given.\n')

#
# Pass 2: copy files over to the staging dir
#
for (fileName, stagingFileName, hasChanged) in filesToProcess:
    if hasChanged:
        if fileName.endswith('mbtiles') or fileName.endswith('terrain') or fileName.endswith('raster') or fileName.endswith('vac'):
            print('\033[1mMove {} to staging dir\033[0m'.format(fileName))
            shutil.move(fileName, stagingFileName)
        else:
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
print("\n\nGenerate maps.json")
maps = []
for fileName in glob.glob(stagingDir + "/**/*.geojson", recursive=True)+glob.glob(stagingDir + "/**/*.mbtiles", recursive=True)+glob.glob(stagingDir + "/**/*.terrain", recursive=True)+glob.glob(stagingDir + "/**/*.raster", recursive=True)+glob.glob(stagingDir + "/**/*.vac", recursive=True)+glob.glob(stagingDir + "/**/*.txt", recursive=True):
    map = {}
    map['path']  = fileName.replace(stagingDir + "/", "")
    t = os.path.getmtime(fileName)
    d = datetime.datetime.fromtimestamp(t)
    map['time'] = ("%04d" % d.year) + ("%02d" % d.month) + ("%02d" % d.day)
    map['size'] = os.path.getsize(fileName)

    #
    # Find the relevant region and add its bounding box to the map
    #
    pureFileName = map['path'].split('/')[-1]
    for region in regions.regions:
        if region['name'] in pureFileName:
            map['bbox'] = region['bbox']
            break
    maps.append(map)

top = {'maps': maps}
top['url'] = serverURL
top['whatsNew'] = whatsNewText
top['minAppVersion'] = minAppVersion
fileName = open(stagingDir + '/maps.json', 'w')
fileName.write(json.dumps(top, sort_keys=True, indent=4))
fileName.close()

#
# Sync the staging dir with the server
#
print('\n\nSync the staging dir with the server @ hetzner')
subprocess.run(
    "rsync -e 'ssh -p222' -vaz --delete "
    + stagingDir
    + "/ akafli@www595.your-server.de:public_html/enroute-data/enroute-GeoJSONv003",
    shell=True,
    check=True
)
