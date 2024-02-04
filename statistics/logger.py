#!/usr/bin/python3

import re
import pickle
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#
# Setup data structures
#

mapAccessNumbers = {}
datesAlreadyProcessed = []

try:
    with open('filename.pickle', 'rb') as f:
        mapAccessNumbers = pickle.load(f)
    datesAlreadyProcessed = mapAccessNumbers.keys()
except:
    print("Cannot read old data.")

file=open(sys.argv[1],"r")

content = file.read()
lines = content.splitlines()

datePattern = r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}'




count = 0
for line in lines:
    if "maps.json" not in line:
        continue

    # Find the date in the log line
    date = re.search(datePattern, line)
    if not date:
        continue
    date_string = date.group(0)
    date = datetime.strptime(date_string, "%d/%b/%Y:%H:%M:%S")
    days_since_epoch = (date - datetime(1970, 1, 1)).days

    if days_since_epoch in datesAlreadyProcessed:
        continue

    if days_since_epoch in mapAccessNumbers:
        mapAccessNumbers[days_since_epoch] = mapAccessNumbers[days_since_epoch]+1
    else:
        mapAccessNumbers[days_since_epoch] = 1

with open('filename.pickle', 'wb') as f:
    pickle.dump(mapAccessNumbers, f)

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(mapAccessNumbers.keys(), mapAccessNumbers.values(), "bo")
plt.ylabel('Users')
#plt.show()
plt.savefig("test.png")
plt.close()
