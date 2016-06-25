#!/bin/bash
cd "`dirname \"$0\"`"
export MY_DIR=`pwd`
cd - >/dev/null 2>&1

cd $MY_DIR
python "$MY_DIR/mtop.py" "$@"