#!/usr/bin/python3

import os
import shutil
import subprocess
import sys
import vector_tile


continents = [
    {'name': 'Africa', 'osmUrl': 'https://download.geofabrik.de/africa-latest.osm.pbf'},
    {'name': 'Asia', 'osmUrl': 'https://download.geofabrik.de/asia/japan-latest.osm.pbf'},
    {'name': 'Australia Oceanica', 'osmUrl': 'https://download.geofabrik.de/australia-oceania-latest.osm.pbf'},
    {'name': 'Europe', 'osmUrl': 'https://download.geofabrik.de/europe-latest.osm.pbf'},
    {'name': 'North America', 'osmUrl': 'https://download.geofabrik.de/north-america-latest.osm.pbf'},
    {'name': 'South America', 'osmUrl': 'https://download.geofabrik.de/south-america-latest.osm.pbf'}
]

regions = [
    {'continent': 'Africa', 'name': 'Canary Islands', 'bbox': [-18.92352, 26.36117, -12.47875, 30.25648]},
    {'continent': 'Africa', 'name': 'Madagascar', 'bbox': [42.30124, -26.5823, 51.14843, -11.36225]},
    {'continent': 'Africa', 'name': 'Namibia', 'bbox': [9.784615, -30.07236, 25.29929, -16.91682]},
    {'continent': 'Africa', 'name': 'South Africa', 'bbox': [15.99606, -47.58493, 39.24259, -22.11736]},

    {'continent': 'Asia', 'name': 'Japan', 'bbox': [122.5607, 21.20992, 153.8901, 45.80245]},

    {'continent': 'Australia Oceanica', 'name': 'Australia', 'bbox': [109.9694, -45.95665, 169.0016, -8.937109]},
    {'continent': 'Australia Oceanica', 'name': 'New Zealand', 'bbox': [162.096, -48.77, 179.8167, -32.667]},

    {'continent': 'Europe', 'name': 'Austria', 'bbox': [9.52678, 46.36851, 17.16273, 49.02403]},
    {'continent': 'Europe', 'name': 'Belgium', 'bbox': [2.340725, 49.49196, 6.411619, 51.59839]},
    {'continent': 'Europe', 'name': 'Bulgaria', 'bbox': [22.34875, 41.22681, 29.18819, 44.22477]},
    {'continent': 'Europe', 'name': 'Croatia', 'bbox': [13.08916, 42.16483, 19.45911, 46.56498]},
    {'continent': 'Europe', 'name': 'Cyprus', 'bbox': [31.95244, 34.23374, 34.96147, 36.00323]},
    {'continent': 'Europe', 'name': 'Czech Republic', 'bbox': [12.08477, 48.54292, 18.86321, 51.06426]},
    {'continent': 'Europe', 'name': 'Denmark', 'bbox': [7.7011, 54.44065, 15.65449, 58.06239]},
    {'continent': 'Europe', 'name': 'Estonia', 'bbox': [20.85166, 57.49764, 28.21426, 59.99705]},
    {'continent': 'Europe', 'name': 'Finland', 'bbox': [19.02427, 59.28783, 31.60089, 70.09959]},
    {'continent': 'Europe', 'name': 'France', 'bbox': [-6.3, 41.27688, 9.8, 51.32937]},
    {'continent': 'Europe', 'name': 'Germany', 'bbox': [5.864417, 47.26543, 15.05078, 55.14777]},
    {'continent': 'Europe', 'name': 'Great Britain', 'bbox': [-9.408655, 49.00443, 2.25, 61.13564]},
    {'continent': 'Europe', 'name': 'Greece', 'bbox': [19.15881, 34.59111, 29.65683, 41.74954]},
    {'continent': 'Europe', 'name': 'Hungary', 'bbox': [16.11262, 45.73218, 22.90201, 48.58766]},
    {'continent': 'Europe', 'name': 'Iceland', 'bbox': [-25.7, 62.84553, -12.41708, 67.50085]},
    {'continent': 'Europe', 'name': 'Ireland and Northern Ireland', 'bbox': [-12.57937, 49.60002, -5.059265, 56.64261]},
    {'continent': 'Europe', 'name': 'Italy', 'bbox': [6.602696, 35.07638, 19.12499, 47.10169]},
    {'continent': 'Europe', 'name': 'Latvia', 'bbox': [20.79407, 55.66886, 28.24116, 58.08231]},
    {'continent': 'Europe', 'name': 'Liechtenstein', 'bbox': [9.471078, 47.04774, 9.636217, 47.27128]},
    {'continent': 'Europe', 'name': 'Lithuania', 'bbox': [20.63822, 53.89605, 26.83873, 56.45106]},
    {'continent': 'Europe', 'name': 'Luxembourg', 'bbox': [5.733033, 49.44553, 6.532249, 50.18496]},
    {'continent': 'Europe', 'name': 'Malta', 'bbox': [14.0988, 35.77776, 14.61755, 36.11909]},
    {'continent': 'Europe', 'name': 'Netherlands', 'bbox': [2.992192, 50.74753, 7.230455, 54.01786]},
    {'continent': 'Europe', 'name': 'Norway', 'bbox': [-11.36801, 57.55323, 35.52711, 81.05195]},
    {'continent': 'Europe', 'name': 'Poland', 'bbox': [14.0998, 48.98568, 24.16522, 55.09949]},
    {'continent': 'Europe', 'name': 'Portugal', 'bbox': [-31.5, 32.0, -6.179513, 42.1639]},
    {'continent': 'Europe', 'name': 'Romania', 'bbox': [20.24181, 43.59703, 30.27896, 48.28633]},
    {'continent': 'Europe', 'name': 'Serbia', 'bbox': [18.82347, 42.24909, 23.00617, 46.19125]},
    {'continent': 'Europe', 'name': 'Slovakia', 'bbox': [16.8284, 47.72646, 22.57051, 49.6186]},
    {'continent': 'Europe', 'name': 'Slovenia', 'bbox': [13.36653, 45.41273, 16.61889, 46.88667]},
    {'continent': 'Europe', 'name': 'Spain', 'bbox': [-9.779014, 35.73509, 5.098525, 44.14855]},
    {'continent': 'Europe', 'name': 'Sweden', 'bbox': [10.54138, 55.02652, 24.22472, 69.06643]},
    {'continent': 'Europe', 'name': 'Switzerland', 'bbox': [5.952882, 45.81617, 10.49584, 47.81126]},

    {'continent': 'North America', 'name': 'Canada', 'bbox': [-141.7761,41.6377, -44.17684, 85.04032]},
    {'continent': 'North America', 'name': 'USA Midwest', 'bbox': [-104.0588, 35.98507, -80.50521, 49.40714]},
    {'continent': 'North America', 'name': 'USA Northeast', 'bbox': [-80.52632, 38.77178, -66.87576, 47.48423]},
    {'continent': 'North America', 'name': 'USA Pacific', 'bbox': [-179.9965, 15.98281, -129.7998, 72.98845]},
    {'continent': 'North America', 'name': 'USA South', 'bbox': [-106.6494, 24.20031, -71.50981, 40.64636]},
    {'continent': 'North America', 'name': 'USA West', 'bbox': [-133.0637, 31.32659, -102.041, 49.45605]},

    {'continent': 'South America', 'name': 'Argentina', 'bbox': [-73.61453, -55.68296, -53.59024, -21.72575]},
    {'continent': 'South America', 'name': 'Brazil', 'bbox': [-74.09056, -35.46552, -27.67249, 5.522895]}
]
