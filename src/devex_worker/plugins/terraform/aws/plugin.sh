#!/bin/bash

if [ -z "$PLUGIN_DIR" ]; then
    export PLUGIN_DIR=$(dirname $0)
fi
python3 $PLUGIN_DIR/plugin.py $@
