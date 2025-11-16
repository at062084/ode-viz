#!/bin/bash

logMsg () {
    DATE=$(date '+%Y-%m-%dT%H:%M:%S')
    CALLER="$(caller)"
    # scripts are usually located in <project>/scripts/<>
    CALL=$(echo $CALLER | awk '{n=split($2,sp,"/"); print sp[n-2]"/"sp[n-1]"/"sp[n]}')
    echo "$DATE INFO [$CALL] $1" | tee -a $ODE_AIRFLOW_LOG
}
