#!/usr/bin/python3

import os
import shutil
import subprocess
import sys
import vector_tile


tasks = [
    ['Africa',
     'https://download.geofabrik.de/africa-latest.osm.pbf',
     [
      ['Canary Islands', [-18.92352, 26.36117, -12.47875, 30.25648]],
      ['Madagascar', [42.30124, -26.5823, 51.14843, -11.36225]],
      ['Namibia', [9.784615, -30.07236, 25.29929, -16.91682]],
      ['South Africa', [15.99606, -47.58493, 39.24259, -22.11736]]
     ]],
    ['Asia',
     'https://download.geofabrik.de/asia/japan-latest.osm.pbf',
     [
      ['Japan', [122.5607, 21.20992, 153.8901, 45.80245]]
     ]],
    ['Australia Oceanica',
     'https://download.geofabrik.de/australia-oceania-latest.osm.pbf',
     [
      ['Australia', [109.9694, -45.95665, 169.0016, -8.937109]],
      ['New Zealand', [162.096, -48.77, 179.8167, -32.667]]
     ]],
    ['Europe',
     'https://download.geofabrik.de/europe-latest.osm.pbf',
     [
      ['Austria', [9.52678, 46.36851, 17.16273, 49.02403]],
      ['Belgium', [2.340725, 49.49196, 6.411619, 51.59839]],
      ['Bulgaria', [22.34875, 41.22681, 29.18819, 44.22477]],
      ['Croatia', [13.08916, 42.16483, 19.45911, 46.56498]],
      ['Cyprus', [31.95244, 34.23374, 34.96147, 36.00323]],
      ['Czech Republic', [12.08477, 48.54292, 18.86321, 51.06426]],
      ['Denmark', [7.7011, 54.44065, 15.65449, 58.06239]],
      ['Estonia', [20.85166, 57.49764, 28.21426, 59.99705]],
      ['Finland', [19.02427, 59.28783, 31.60089, 70.09959]],
      ['France', [-6.3, 41.27688, 9.8, 51.32937]],
      ['Germany', [5.864417, 47.26543, 15.05078, 55.14777]],
      ['Great Britain', [-9.408655, 49.00443, 2.25, 61.13564]],
      ['Greece', [19.15881, 34.59111, 29.65683, 41.74954]],
      ['Hungary', [16.11262, 45.73218, 22.90201, 48.58766]],
      ['Iceland', [-25.7, 62.84553, -12.41708, 67.50085]],
      ['Ireland and Northern Ireland', [-12.57937, 49.60002, -5.059265, 56.64261]],
      ['Italy', [6.602696, 35.07638, 19.12499, 47.10169]],
      ['Latvia', [20.79407, 55.66886, 28.24116, 58.08231]],
      ['Liechtenstein', [9.471078, 47.04774, 9.636217, 47.27128]],
      ['Lithuania', [20.63822, 53.89605, 26.83873, 56.45106]],
      ['Luxembourg', [5.733033, 49.44553, 6.532249, 50.18496]],
      ['Malta', [14.0988, 35.77776, 14.61755, 36.11909]],
      ['Netherlands', [2.992192, 50.74753, 7.230455, 54.01786]],
      ['Norway', [-11.36801, 57.55323, 35.52711, 81.05195]],
      ['Poland', [14.0998, 48.98568, 24.16522, 55.09949]],
      ['Portugal', [-31.5, 32.0, -6.179513, 42.1639]],
      ['Romania', [20.24181, 43.59703, 30.27896, 48.28633]],
      ['Serbia', [18.82347, 42.24909, 23.00617, 46.19125]],
      ['Slovakia', [16.8284, 47.72646, 22.57051, 49.6186]],
      ['Slovenia', [13.36653, 45.41273, 16.61889, 46.88667]],
      ['Spain', [-9.779014, 35.73509, 5.098525, 44.14855]],
      ['Sweden', [10.54138, 55.02652, 24.22472, 69.06643]],
      ['Switzerland', [5.952882, 45.81617, 10.49584, 47.81126]]
     ]],
    ['North America',
     'https://download.geofabrik.de/north-america-latest.osm.pbf',
     [
         ['Canada', [-141.7761,41.6377, -44.17684, 85.04032]],
         ['USA Midwest', [-104.0588, 35.98507, -80.50521, 49.40714]],
         ['USA Northeast', [-80.52632, 38.77178, -66.87576, 47.48423]],
         ['USA Pacific', [-179.9965, 15.98281, -129.7998, 72.98845]],
         ['USA South', [-106.6494, 24.20031, -71.50981, 40.64636]],
         ['USA West', [-133.0637, 31.32659, -102.041, 49.45605]]
     ]],
    ['South America',
     'https://download.geofabrik.de/south-america-latest.osm.pbf',
     [
         ['Argentina', [-73.61453, -55.68296, -53.59024, -21.72575]],
         ['Brazil', [-74.09056, -35.46552, -27.67249, 5.522895]]
     ]]
]

for task in tasks:
    continent = task[0]
    maps = task[2]
    print('Download {}'.format(continent))
    try:
        os.remove('download.pbf')
    except BaseException as err:
        True
    print(task[1])
    subprocess.run(['curl', task[1], "-L", "--output", "download.pbf"], check=True)

    print('Run Osmium tags-filter')
    subprocess.run(
        ["osmium",
        "tags-filter",
        'download.pbf',
        "/aerialway=cable_car,gondola,zip_line,goods",
        "/aeroway",
        "/admin_level=2",
        "/highway=motorway,trunk,primary,secondary,motorway_link",
        "/landuse",
        "/natural",
        "/place=city,town,village",
        "/railway",
        "/water",
        "/waterway",
        "-o", "out.pbf",
        "--overwrite"],
        check=True
    )
    os.remove('download.pbf')
    
    for map in maps:
        country = map[0]
        bbox = map[1]
        vector_tile.pbf2mbtiles('out.pbf', bbox[0], bbox[1], bbox[2], bbox[3], country)
        try:
            os.remove("out/"+continent+"/"+country+'.mbtiles')
        except BaseException as err:
            True
        os.makedirs("out/"+continent, exist_ok=True)
        os.replace(country+'.mbtiles', "out/"+continent+"/"+country+'.mbtiles')
    os.remove('out.pbf')
