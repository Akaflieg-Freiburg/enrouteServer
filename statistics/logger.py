import re
import pickle
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

file=open("access.log.1","r")

content = file.read()
lines = content.splitlines()

datePattern = r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}'


mapAccessNumbers = {}


count = 0
for line in lines:
    if "maps.json" not in line:
        continue
    # Find the date in the log line
    date = re.search(datePattern, line)
    if not date:
        continue

    count = count + 1

    date_string = date.group(0)
    date = datetime.strptime(date_string, "%d/%b/%Y:%H:%M:%S")

    # Convert the datetime object to days since the epoch
    days_since_epoch = (date - datetime(1970, 1, 1)).days
    if days_since_epoch in mapAccessNumbers:
        mapAccessNumbers[days_since_epoch] = mapAccessNumbers[days_since_epoch]+1
    else:
        mapAccessNumbers[days_since_epoch] = 1

mapAccessNumbers[19755] = 800
mapAccessNumbers[19757] = 850


with open('filename.pickle', 'wb') as f:
    pickle.dump(mapAccessNumbers, f)

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(mapAccessNumbers.keys(), mapAccessNumbers.values(), "bo")
plt.ylabel('Users')
plt.show()