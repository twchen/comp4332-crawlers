#!/usr/bin/env bash

cd ~/git-repos/hkust_courses
python3 ./main.py
cd snapshots
git add .
git commit -m "added new snapshot at $(TZ=Hongkong date +%m-%d\ %H:%M)"
git push

