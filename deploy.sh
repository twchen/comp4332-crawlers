#!/usr/bin/env bash

#pip install -r requirements.txt
(crontab -l 2>/dev/null; echo "0,30 * * * * bash -c \"cd $(pwd) && python main.py\"") | crontab -

