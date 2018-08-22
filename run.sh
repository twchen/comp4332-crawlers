#!/usr/bin/env bash
BASEDIR=$(dirname "$BASH_SOURCE")
VIRTUAL_ENV_DIR=$BASEDIR/pyhome

source $VIRTUAL_ENV_DIR/bin/activate
TZ=Hongkong date "+%m-%d %H:%M"
cd $BASEDIR && python main.py
