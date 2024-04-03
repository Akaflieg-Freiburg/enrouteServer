#!/bin/bash

#
# Fail on first error
#

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"
cd statistics
./logger.py /var/log/apache2/access.log.1
./visualizer.py
mv *.png /var/www/storage/
