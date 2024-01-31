#!/usr/bin/env bash

sudo virsh destroy --domain testvm1
sudo virsh undefine --domain testvm1
sudo zfs destroy zroot/zk/testvm1-root
