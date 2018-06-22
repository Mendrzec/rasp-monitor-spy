#!/bin/bash

if [ ! -e /etc/init/raspmonitor.conf ]; then
    echo "You must install raspmonitor first!"
fi

cd /opt/raspmonitor/
${PYTHON} raspmonitor.py