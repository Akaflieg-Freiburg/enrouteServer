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


fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(mapAccessNumbers.keys(), mapAccessNumbers.values(), "bo")
plt.suptitle('Users per day')
plt.ylabel('Users')
plt.show()
#plt.savefig("test.png")
plt.close()

fig, ax = plt.subplots()
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
plt.plot(trafficNumbers.keys(), trafficNumbers.values(), "bo")
plt.suptitle('Traffic per day')
plt.ylabel('Traffic')
plt.show()
#plt.savefig("test.png")
plt.close()
