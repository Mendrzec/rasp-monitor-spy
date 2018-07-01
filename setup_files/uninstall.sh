#!/bin/bash

readonly ETC_SERVICE_FILE="/etc/systemd/system/raspmonitor.service"

function exitWithError {
    >&2 echo "$1"
    exit 1
}

function removeFile {
    local file=$1
    if [ -e ${file} ]; then
        rm -rvf ${file}
    fi
}
function checkIfSudo {
    if [ $(id -u) != 0 ]; then
        exitWithError "Must be run as sudo user!"
    fi
}

function checkIfAlreadyUninstalled {
    if [ ! -e ${ETC_SERVICE_FILE} ]; then
        exitWithError "It seems that raspmonitor is already uninstalled. Nothing to do."
    fi
}

checkIfSudo
checkIfAlreadyUninstalled

systemctl stop raspmonitor.service
removeFile ${ETC_SERVICE_FILE}

removeFile "/opt/raspmonitor/spy"
removeFile "/opt/raspmonitor/raspmonitor.py"
removeFile "/opt/raspmonitor/launcher.sh"
