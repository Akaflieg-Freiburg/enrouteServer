#!/bin/bash

#
# Fail on first error
#

set -e


cd scripts
./generateWorldAviationMap.py
./splitAviationMap.py
./generateFlarmDB.py

./deploy.py
