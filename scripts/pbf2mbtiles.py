#!/bin/python3

import math
import os
import subprocess
import sys
import vector_tile



def pbf2mbtiles(pbfFileName, lonNW, latNW, lonSE, latSE, mbtilesFileName):
  """Converts openstreetmap PBF file into mbtiles

  This method converts a PBF file with openstreetmap data into an mbtiles file.
  The output contains tiles for zoom level 7--10 and it optimized for use with
  the enrouteMap style.

  The coordiante arguments specify a bounding box. The box is enlarged to fit
  zoom level 7 tile boundaries. This way, it is ensured that the output does not
  contain any half-filled tiles.

  :param pbfFileName: Name of input file

  :param latNW: latitude of NW edge of bounding box

  :param lonNW: longitude of NW edge of bounding box

  :param latSE: latitude of SE edge of bounding box

  :param lonSE: longitude of SE edge of bounding box

  :param pbfFileName: Name of output file, will be overwritten if exists

  """

  def deg2num(lat_deg, lon_deg, zoom):
    """
    Converts coordinate to tile number
    taken from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon..2Flat._to_tile_numbers_2
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

  def num2deg(xtile, ytile, zoom):
    """
    Converts tile number to coordinate
    taken from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon..2Flat._to_tile_numbers_2
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


  (x, y) = deg2num(latNW, lonNW, 7.0)
  (extLatNW, extLonNW) = num2deg(x, y+1, 7.0)
  (x, y) = deg2num(latSE, lonSE, 7.0)
  (extLatSE, extLonSE) = num2deg(x+1, y, 7.0)

  print('Run Osmium extract')
  subprocess.run(
    "osmium extract --bbox {},{},{},{} {} -o bboxed.pbf --overwrite".format(extLonNW, extLatNW, extLonSE, extLatSE, pbfFileName),
    shell=True,
    check=True,
  )

  print('Run tilemaker')
  subprocess.run(
    "tilemaker --config tilemaker/config.json --process tilemaker/process.lua --bbox {},{},{},{} --input bboxed.pbf --output {}".format(lonNW, latNW, lonSE, latSE, mbtilesFileName),
    shell=True,
    check=True
  )
  os.remove("bboxed.pbf")

  print('Optimize')
  vector_tile.optimizeMBTILES(mbtilesFileName)
