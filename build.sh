#!/bin/bash

.venv/bin/python src/station.py &&
    ../yagl/build/yagl -d station.grf &&
    echo "$(date -u '+%Y-%m-%d %H:%M:%S %z') $(md5sum station.grf)" >> build.log &&
    cp station.grf ~/.local/share/openttd/newgrf &&
    echo "copied"
