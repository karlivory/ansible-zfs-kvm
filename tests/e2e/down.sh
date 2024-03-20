#!/usr/bin/env bash

sudo virsh destroy --domain testvm-debian11
sudo virsh destroy --domain testvm-debian12
sudo virsh destroy --domain testvm-ubuntu2204
sudo virsh destroy --domain testvm-opensuseleap
sudo virsh destroy --domain testvm-rocky9

sleep 2

sudo virsh undefine --domain testvm-debian11
sudo virsh undefine --domain testvm-debian12
sudo virsh undefine --domain testvm-ubuntu2204
sudo virsh undefine --domain testvm-opensuseleap
sudo virsh undefine --domain testvm-rocky9

sleep 2

sudo zfs destroy zroot/zk/testvm-debian11-root
sudo zfs destroy zroot/zk/testvm-debian12-root
sudo zfs destroy zroot/zk/testvm-ubuntu2204-root
sudo zfs destroy zroot/zk/testvm-opensuseleap-root
sudo zfs destroy zroot/zk/testvm-rocky9-root

sudo zfs destroy zroot/zk/testvm-debian11-data
sudo zfs destroy zroot/zk/testvm-debian12-data
sudo zfs destroy zroot/zk/testvm-ubuntu2204-data
sudo zfs destroy zroot/zk/testvm-opensuseleap-data
sudo zfs destroy zroot/zk/testvm-rocky9-data
