#!/bin/bash

/home/jeremy/Documents/code/wers/.venv/bin/python /home/jeremy/Documents/code/wers/src/station.py &&
    ../yagl/build/yagl -d station.grf &&
    rm -r station &&
    grftopy station.grf &&
    cp station.grf ~/.local/share/openttd/newgrf &&
    echo "copied"
