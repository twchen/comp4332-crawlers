#!/usr/bin/env bash

cd $(dirname "$BASH_SOURCE")
source configvars
if [ "$GIT_PUSH" = true ]; then
    if [ ! -f "snapshots_dir" ]; then
        mkdir snapshots_dir
    fi
    cd snapshots_dir
    if [ ! -f ".git" ]; then
        git init .
        git remote add origin $GIT_URL
        git branch --set-upstream-to origin/master
    fi
fi
chmod +x run.sh

# set up a python 3 virtual environment
virtualenv -p python3 pyhome
cd pyhome
source bin/activate
pip install -r ../requirements.txt

# set up a cron job to crawl snapshots at MINUTES
BASEDIR=$(pwd)
(crontab -l 2>/dev/null; echo "$MINUTES * * * * cd $BASEDIR && (./run.sh 2>>err.txt 1>>info.txt)") | crontab -
