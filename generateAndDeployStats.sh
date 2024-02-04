#!/bin/bash

#
# Fail on first error
#

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"
cd statistics
./logger.py /var/log/apache2/access.log.1
mv test.png /var/www/storage/users_per_day.png
