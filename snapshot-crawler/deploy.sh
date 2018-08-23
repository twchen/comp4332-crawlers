#!/usr/bin/env bash

cd $(dirname "$BASH_SOURCE")
BASEDIR=$(pwd)
source configvars
if [ "$GIT_PUSH" = true ]; then
    if [ ! -f "all-snapshots" ]; then
        mkdir all-snapshots
    fi
    cd all-snapshots
    if [ ! -f ".git" ]; then
        git init .
        git remote add origin $GIT_URL
        git pull
        git branch -u origin/master
    fi
    cd ..
fi
chmod +x run.sh

# set up a python 3 virtual environment
virtualenv -p python3 pyhome
cd pyhome
source bin/activate
pip install -r ../requirements.txt

# set up a cron job to crawl snapshots at MINUTES
(crontab -l 2>/dev/null; echo "$MINUTES * * * * cd $BASEDIR && (./run.sh 2>>err.txt 1>>info.txt)") | crontab -
