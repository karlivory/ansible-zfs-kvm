#!/usr/bin/env bash

set -eux

# ANSIBLE_ROLES_PATH=..

for i in $(seq 1 2); do
  ansible-playbook test.yml -e "test_no=$i" -i "tests/$i/inventory.yml" -v "$@"
done
