#!/usr/bin/python3

import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#
# Setup data structures
#

mapAccessNumbers = {}

with open('filename.pickle', 'rb') as file:
    mapAccessNumbers = pickle.load(file)
    trafficNumbers = pickle.load(file)
    metarAccessNumbers = pickle.load(file)
    notamAccessNumbers = pickle.load(file)

trafficNumbersInGB = {}
for date in trafficNumbers:
    trafficNumbersInGB[date] = trafficNumbers[date]/1000000000.0

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(mapAccessNumbers.keys(), mapAccessNumbers.values(), "bo")
plt.suptitle('Users per day')
plt.ylabel('Users')
plt.savefig("users-per-day.png")
plt.close()

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(metarAccessNumbers.keys(), metarAccessNumbers.values(), "bo")
plt.suptitle('METAR downloads per day')
plt.ylabel('METAR downloads')
plt.savefig("metar-downloads-per-day.png")
plt.close()

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(notamAccessNumbers.keys(), notamAccessNumbers.values(), "bo")
plt.suptitle('NOTAM downloads per day')
plt.ylabel('NOTAM downloads')
plt.savefig("notam-downloads-per-day.png")
plt.close()

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(trafficNumbersInGB.keys(), trafficNumbersInGB.values(), "bo")
plt.suptitle('Traffic per day')
plt.ylabel('Traffic (in GB)')
#plt.show()
plt.savefig("traffic-per-day.png")
plt.close()
