#!/bin/sh
apt-get update -y
apt-get dist-upgrade -y

git clone https://github.com/lthiery/SPI-Py.git
cd SPI-Py
python3 setup.py install
cd ../
rm SPI-Py -rf

pip3 install psutil

# TODO: whether rasp monitor is running as root or not apropriate permissions must be set for dirs
mkdir logs
mkdir stats_not_sent