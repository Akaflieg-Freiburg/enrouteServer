#!/bin/python3

import math
import os
import subprocess
import sys
import vector_tile


def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)


bboxStringList = sys.argv[2].split(",")
bboxList = list(map(float, bboxStringList))

(x, y) = deg2num(bboxList[1], bboxList[0], 7.0)
(latNW, lonNW) = num2deg(x, y+1, 7.0)
(x, y) = deg2num(bboxList[3], bboxList[2], 7.0)
(latSE, lonSE) = num2deg(x+1, y, 7.0)

print('Run Osmium extract')
subprocess.run(
    "osmium extract --bbox {},{},{},{} {} -o bboxed.pbf --overwrite".format(lonNW, latNW, lonSE, latSE, sys.argv[1]),
    shell=True,
    check=True,
)

print('Run tilemaker')
subprocess.run(
    "tilemaker --bbox {} --input bboxed.pbf --output {}".format(sys.argv[2], sys.argv[3]),
    shell=True,
    check=True
)
os.remove("bboxed.pbf")

print('Optimize')
vector_tile.optimizeMBTILES(sys.argv[3])
