#!/bin/bash

cd scripts
./generateWorldAviationMap.py
./splitAviationMap.py
./generateFlarmDB.py

./deploy.py
