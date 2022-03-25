#!/bin/bash

#
# Fail on first error
#

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"
cd scripts
./generateWorldAviationMap.py
./splitAviationMap.py
./generateFlarmDB.py
./deploy.py