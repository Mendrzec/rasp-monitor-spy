#!/bin/bash

function exitWithError {
    >&2 echo "$1"
    exit 1
}

function checkPythonVersion {
    local python_command=$1
    local version=$(${python_command} -V 2>&1 | cut -d ' ' -f 2)
    if [[ ${version} == 3\.* ]]; then
        >&2 echo "Python version ${version} found!"
        return ${TRUE}
    fi
    return ${FALSE}
}

function getPythonAndPipCommand {
    if checkPythonVersion "python"; then
        echo "python pip"
        return ${TRUE}
    fi

    if checkPythonVersion "python3"; then
        echo "python3 pip3"
        return ${TRUE}
    fi

    exitWithError "Python not found or version is too low (Python 3.5+ required)"
}

function makeDir {
    local dir=$1
    if [ ! -d ${dir} ]; then
        mkdir -v ${dir}
        chmod 775 ${dir}
        chown pi:pi ${dir}
    fi
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

function checkIfAlreadyInstalled {
    if [ -e ${ETC_SERVICE_FILE} ]; then
        exitWithError "It seems that raspmonitor is already installed. Uninstall it first."
    fi
}