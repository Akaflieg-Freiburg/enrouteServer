#!/usr/bin/python3

from datetime import datetime

import pickle
import re
import shlex
import sys


#
# Setup data structures
#

# keys: days_since_epoch, values: number that maps.json has been downloaded on that day
mapAccessNumbers = {}

# keys: days_since_epoch, values: traffic on that day
trafficNumbers = {}

# values: days since epoch
datesAlreadyProcessed = []

try:
    with open('filename.pickle', 'rb') as f:
        mapAccessNumbers = pickle.load(f)
        trafficNumbers = pickle.load(f)
    datesAlreadyProcessed = sorted(mapAccessNumbers.keys())
except:
    print("Cannot read old data.")

file=open(sys.argv[1],"r")

content = file.read()
lines = content.splitlines()

datePattern = r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}'
downloadSizePattern = r'\s(\d+)\s*$'

count = 0
for line in lines:
    count = count + 1
    
    lineItems = shlex.split(line)

    # Find the date in the log line
    date = re.search(datePattern, line)
    if not date:
        continue
    date_string = date.group(0)
    date = datetime.strptime(date_string, "%d/%b/%Y:%H:%M:%S")
    days_since_epoch = (date - datetime(1970, 1, 1)).days

    # Skip entries for days that have already been processed
#    if days_since_epoch in datesAlreadyProcessed:
#        continue

    # Count times that maps.json has been downloaded
    if "maps.json" in line:
        if days_since_epoch in mapAccessNumbers:
            mapAccessNumbers[days_since_epoch] = mapAccessNumbers[days_since_epoch]+1
        else:
            mapAccessNumbers[days_since_epoch] = 1

    if "enroute" in line:
        traffic = int(lineItems[7])
        if days_since_epoch in trafficNumbers:
            trafficNumbers[days_since_epoch] = trafficNumbers[days_since_epoch]+traffic
        else:
            trafficNumbers[days_since_epoch] = traffic

print(trafficNumbers)

with open('filename.pickle', 'wb') as f:
    pickle.dump(mapAccessNumbers, f)
    pickle.dump(trafficNumbers, f)
