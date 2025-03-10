#!/bin/bash

#
# Fail on first error
#

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"
cd scripts
python3 ./generateWorldRasterMaps.py
python3 ./generateWorldAviationMap.py
python3 ./splitAviationMap.py
python3 ./deploy-hetzner.py
