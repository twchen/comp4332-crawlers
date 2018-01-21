#!/usr/bin/env bash
BASEDIR=$(dirname "$BASH_SOURCE")
VIRTUAL_ENV_DIR=$BASEDIR/../pyhome

source $VIRTUAL_ENV_DIR/bin/activate
cd $BASEDIR
python ./main.py
