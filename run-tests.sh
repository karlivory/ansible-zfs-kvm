#!/bin/bash

set -e

ansible-test units --requirements
ansible-test integration
