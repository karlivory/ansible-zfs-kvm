#!/usr/bin/env bash

set -eu

fail() {
    echo "ERROR! $1" >&2
    echo "Aborting..." >&2
    exit 1
}

check_python() {
    command -v python3 >/dev/null 2>&1 || fail "Python is required but it's not installed."

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}') || fail "Failed to fetch Python version"
    PYTHON_MAJOR_VERSION=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    PYTHON_MINOR_VERSION=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR_VERSION" -lt 3 ] || { [ "$PYTHON_MAJOR_VERSION" -eq 3 ] && [ "$PYTHON_MINOR_VERSION" -lt 9 ]; }; then
      fail "Python version 3.9 or higher is required (installed: Python $PYTHON_VERSION)"
    fi
}

setup_venv() {
    command -v virtualenv >/dev/null 2>&1 || fail "virtualenv is required but it's not installed."
    command -v pip >/dev/null 2>&1 || fail "pip is required but it's not installed."

    if [ ! -d venv ]; then
        echo "Creating a virtual environment..."
        virtualenv venv
    fi

    source venv/bin/activate

    echo "Installing pip requirements..."
    pip install -r "./test-requirements.txt"
}


check_python
setup_venv

export ANSIBLE_FORCE_COLOR=1
export ANSIBLE_HOST_KEY_CHECKING=False

ansible-test units --requirements
ansible-test integration
