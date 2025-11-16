#!/usr/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BASE_DIR=$SCRIPT_DIR

IMG_BASENAME="ode"
IMG_BUILDNAME="airflow"

[ $# -ge 1 ] && IMG_BUILDNAME=$1

mkdir -p $BASE_DIR/log 2>/dev/null
LOG="$BASE_DIR/log/build.$IMG_BUILDNAME.log"

echo "==============================================================" >> $LOG
echo "$(date +%Y-%m-%d %H:%M:%S)" >> $LOG
echo "==============================================================" >> $LOG

podman build -t $IMG_BASENAME-$IMG_BUILDNAME -f $BASE_DIR/Dockerfile ./$BASE_DIR 2>&1 | tee -a $LOG