#!/bin/bash

#
# Fail on first error
#

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"
cd scripts
python3 ./generateFlarmDB.py
python3 ./deploy-hetzner.py
