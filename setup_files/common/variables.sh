#!/bin/bash

# /opt/raspmonitor
#           |_ logs
#           |_ stats_not_sent
#           |_ spy
#           |   \_ ...
#           |_setup
#           |   \_uninstall.sh
#           |_ raspmonitor.py

readonly TRUE=0
readonly FALSE=1

readonly RASP_ROOT_DIR="/opt/raspmonitor"
readonly LOGS_DIR="${RASP_ROOT_DIR}/logs"
readonly NOT_SENT_DIR="${RASP_ROOT_DIR}/stats_not_sent"
readonly SPY_DIR="${RASP_ROOT_DIR}/spy"
readonly LAUNCHER_FILE="${RASP_ROOT_DIR}/launcher.sh"

readonly ETC_SERVICE_FILE="/etc/systemd/system/raspmonitor.service"

PYTHON=
PIP=