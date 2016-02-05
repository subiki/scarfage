#!/bin/bash

echo "$0 Starting..."

echo "Activating venv..."
. $(dirname $0)/.venv/bin/activate

pip list

# GNDN

echo "$0 Finished!"
