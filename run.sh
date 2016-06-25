#!/usr/bin/env bash
#set -vx

cd "`dirname \"$0\"`"
export MY_DIR=`pwd`
#cd - >/dev/null 2>&1

python "$MY_DIR/am.monitors.smartcontrollerwrapper.py" "$@"