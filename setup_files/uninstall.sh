#!/bin/bash

. common/functions.sh

checkIfSudo

systemctl stop raspmonitor.service
removeFile "/etc/systemd/system/raspmonitor.service"

removeFile "/opt/raspmonitor/spy"
removeFile "/opt/raspmonitor/raspmonitor.py"
removeFile "/opt/raspmonitor/launcher.sh"
