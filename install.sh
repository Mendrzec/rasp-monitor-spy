#!/bin/bash

. setup_files/common/functions.sh
. setup_files/common/variables.sh

function installSpiPy {
    cd setup_files/vendor/SPI-Py
    ${PYTHON} setup.py install
    cd ../../../
    rm setup_files/vendor/SPI-Py -rf
}

checkIfSudo
checkIfAlreadyInstalled

# requirements
PYTHON_AND_PIP_COMMAND=$(getPythonAndPipCommand)
PYTHON=$(cut -d ' ' -f 1 <<< ${PYTHON_AND_PIP_COMMAND})
PIP=$(cut -d ' ' -f 2 <<< ${PYTHON_AND_PIP_COMMAND})

# dependencies
apt-get update -y
apt-get dist-upgrade -y

installSpiPy
${PIP} install psutil

# make dirs and copy files
makeDir ${RASP_ROOT_DIR}
makeDir ${LOGS_DIR}
makeDir ${NOT_SENT_DIR}

# spy dir and raspmonitor.sh -> /opt/raspmonitor
cp -rv "raspmonitor/"* ${RASP_ROOT_DIR}
chown -R pi:pi ${RASP_ROOT_DIR}

# uninstall.sh -> /opt/raspmonitor
cp -rv "setup_files/uninstall.sh" ${RASP_ROOT_DIR}
chmod 775 "${RASP_ROOT_DIR}/uninstall.sh"

# autostart
cp -v "setup_files/raspmonitor.service" /etc/systemd/system/
sed -i "s/\${PYTHON}/${PYTHON}/" ${ETC_SERVICE_FILE}

systemctl enable raspmonitor.service
systemctl start raspmonitor.service
systemctl daemon-reload
systemctl status raspmonitor.service