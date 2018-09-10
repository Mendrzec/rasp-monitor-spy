#!/bin/bash

function exitWithError {
    >&2 echo "$1"
    exit 1
}

function checkIfSudo {
    if [ $(id -u) != 0 ]; then
        exitWithError "Must be run as sudo user!"
    fi
}

checkIfSudo

RASPMONITOR_REPOSITORY_PATH=${1}
if [ -z "${RASPMONITOR_REPOSITORY_PATH}" ]; then
    exitWithError "Please provide path to rasp-monitor-spy directory as an argument."
fi

echo "Please enter an authorization token:"
read -s AUTH_TOKEN
if [ -z "${AUTH_TOKEN}" ]; then
    exitWithError "Auth token is empty"
fi

echo "### Uninstalling previous version of raspmonitor"
pushd /opt/raspmonitor
bash uninstall.sh
popd

echo "### Updating repository to the latest tag"
cd ${RASPMONITOR_REPOSITORY_PATH}
git pull https://Mendrzec:${AUTH_TOKEN}@github.com/Mendrzec/rasp-monitor-spy.git
git checkout -- .
LATEST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1))
git checkout ${LATEST_TAG}

echo "### Installing latest version of raspmonitor"
bash install.sh --update
