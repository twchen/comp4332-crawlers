#!/usr/bin/env bash

hour=$(TZ=Hongkong date "+%k")
minute=$(TZ=Hongkong date "+%M")
if (( hour == 8 || (hour == 9 && minute < 30) )); then
    exit 0
fi

cd $(dirname "$BASH_SOURCE")
source configvars
BASEDIR=$(pwd)
VIRTUAL_ENV_DIR=$BASEDIR/pyhome

source $VIRTUAL_ENV_DIR/bin/activate
TZ=Hongkong date "+%m-%d %H:%M"
if [ "$GIT_PUSH" = true ]; then
    main_args="-p"
fi
cd $BASEDIR && python main.py $main_args

if [ -s err.txt -a "$NOTIFY_ERROR" = true ]; then
    python send_email.py -u $SENDER_EMAIL -p $SENDER_PASSWD -t $RECEIVER_EMAIL -s $SMTP_SERVER 1>&2
    rm err.txt
fi
