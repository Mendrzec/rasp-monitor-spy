#!/bin/bash

. setup_files/common/functions.sh
. setup_files/common/variables.sh

function installSpiPy {
    pushd setup_files/vendor/SPI-Py
    ${PYTHON} setup.py install
    popd
    rm setup_files/vendor/SPI-Py -rf
}

checkIfSudo
checkIfAlreadyInstalled

# set hostname
echo "#############################"
echo "### RASPMONITOR INSTALLER ###"
echo "#############################"
echo

# collect required input data
echo "Please enter machine name:"
read NEW_HOSTNAME

echo "Please enter server ip and port (format http://ip:port/)"
read SERVER_URL
while [ -z "$(echo ${SERVER_URL} | grep ^http://.*:.*/$)" ]; do
    echo "Entered url: ${SERVER_URL} has wrong format. Try again."
    read SERVER_URL
done

# enable ssh
echo "### Enabling SSH..."
systemctl enable ssh.service
systemctl start ssh.service
systemctl status ssh.service

# enable spi
echo "### Enabling SPI..."
sed -i "s/#dtparam=spi=on/dtparam=spi=on/" /boot/config.txt

#Localtime
echo "### Setting timezone..."
sudo cp /usr/share/zoneinfo/Poland /etc/localtime

# dependencies
apt-get update -y
apt-get install python3-dev python3-pip python3-rpi.gpio -y

# requirements
echo "### Looking for Python version..."
PYTHON_AND_PIP_COMMAND=$(getPythonAndPipCommand)
PYTHON=$(cut -d ' ' -f 1 <<< ${PYTHON_AND_PIP_COMMAND})
PIP=$(cut -d ' ' -f 2 <<< ${PYTHON_AND_PIP_COMMAND})

echo "### Installing SpiPy library..."
installSpiPy
${PIP} install psutil
${PIP} install requests

# set host name
echo "### Setting new hostname..."
sed -i "s/raspberrypi/${NEW_HOSTNAME}/" /etc/hostname
sed -i "s/raspberrypi/${NEW_HOSTNAME}/" /etc/hosts
/etc/init.d/hostname.sh start

# edit settings.py to set server url
SERVER_URL_COMP=$(echo ${SERVER_URL} | sed "s#/#\\\\/#g")
sed -i "s/SERVER_URL.*/SERVER_URL = \"${SERVER_URL_COMP}\"/" raspmonitor/spy/settings.py

# make dirs and copy files
echo "### Copying data..."
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

echo "### Starting raspmonitor..."
systemctl enable raspmonitor.service
systemctl daemon-reload
systemctl status raspmonitor.service

echo "### Rebooting..."
shutdown -r now