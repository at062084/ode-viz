#!/bin/bash

# Download Dataset file from URL into local folder structure
# Called from airflow DAG in stage 'download'
# Parameters:
#   $1: dsURL
#   $2: dsFILE 
#   $3: mode [file|redirect]
#   $4: dsDIR

#-----------------------------------------------------------------------------------
# Load default env: *_ROOT_DIRs and logMsg
#-----------------------------------------------------------------------------------
if [ ! -r $INVENTORY_ROOT_DIR/inventory.sh ]
then
    echo "ERROR: Cannot read $INVENTORY_ROOT_DIR/inventory.sh"
    exit 1
fi
source $INVENTORY_ROOT_DIR/inventory.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BASE_DIR=$SCRIPT_DIR/../../

CUR_DIR=$(pwd)
cd $BASE_DIR

logMsg "Executing $0 $@ in $CUR_DIR and changing to $BASE_DIR"

python -c "import os; print('\n'.join(sorted(f'{k}={v}' for k, v in os.environ.items())))" >> /tmp/download.dataset.sh.log

# Need filename
if [ $# -lt 4 ] 
then
    logMsg "ERROR: Missing at least one of the three required parameter Url, Dirs and Filename"
    cd $CUR_DIR
    exit 1
fi

# Parameters
dsURL="$1"
dsFILE="$2"
dsMode="$3"
dsDIR="$4"


# --------------------------------------------------------------------------
# Add nodes to lineage log
# --------------------------------------------------------------------------
add_ultimate_source () {
    # Call Python lineage tracking script
    python3 $INVENTORY_ROOT_DIR/scripts/python/datalineage_bash.py \
        "$0" \
        "$ultURL" \
        "download/$dsDIR/$dsFILE"
}

# Always add lineage tracking
# Extract host from http://<url>/...
ultURL=$(echo $dsURL | awk '{n=split($0,sp,"?");print sp[1]}')
# ultURL=$(echo $dsURL | awk '{n=split($0,sp,"/");if(n>2)print sp[3]; else print $0}')
add_ultimate_source


# --------------------------------------------------------------------------
# Direct downoad of cvs file
# --------------------------------------------------------------------------
if [ "$dsMode" == "file" ]
then
    # Filename in local Filesystem and remote http server
    srcURL="$dsURL/$dsFILE"
    dstFILE="$DATA_DOWNLOAD_DIR/$dsDIR/$dsFILE"

    # dstFile may or not exist already
    if [ -r $dstFile ]
    then
        logMsg "Checking $dstFILE for updates"
        localFileSize="$(ls -l $dstFILE 2>&1 | awk '{print $5}')" 
        # Get remote filesize and remove trailing cr
        remoteFileSize="$(curl -sI $srcURL 2>&1 |awk '/Content-Length/ {print substr($2,1,length($2)-1)}')"
        logMsg "Local filesize: <$localFileSize>  Remote filesize: <$remoteFileSize>"
    else
        logMsg "ENOTFOUND: $dstFILE does not exist"
        localFileSize="0" 
    fi

    # Download dataset
    if [ "$localFileSize" != "$remoteFileSize" ]
    then
        logMsg "Downloading $srcURL"
        curl --no-progress-meter -o "$dstFILE" "$srcURL"
        RC=$?
        cd $CUR_DIR
        # Check for curl technical error
        if [ $RC -ne 0 ]
        then
            logMsg "Cannot download $srcFILE. Skipping"
            # Indicate SKIP to airflow
            RC=99
        fi

    # Return 99 in case no update. Like this indicate to caller any subsequent ETL pipeline must not be started
    else 
        logMsg "Skipping $dstFILE"
        cd $CUR_DIR
        # Indicate SKIP to airflow
        RC=99
    fi
fi



# --------------------------------------------------------------------------
# Direct downoad of cvs file
# In mode hashed, the download URL containes the complete download link including a hash of the filename
# The filename to use locally is given in dsFILE
# --------------------------------------------------------------------------
if [ "$dsMode" == "redirect" ]
then
    # Filename in local Filesystem and remote http server
    srcURL="$dsURL"
    dstDIR="$DATA_DOWNLOAD_DIR/$dsDIR"
    dstFILE="$DATA_DOWNLOAD_DIR/$dsDIR/$dsFILE"
    mkdir -p $dstDIR 2>/dev/null

    # For now, skip checks on existence or size of local/remote file 
    logMsg "Downloading $dstFILE"
    # Extract redirection URL 
    logMsg "srcURL=$srcURL"
    # Must remove trailing CRLF from curl Location output
    fwdURL=$(curl -vkil --no-progress-meter $srcURL 2>&1 | awk '{if($1=="Location:")print substr($2,1,length($2)-1)}')
    logMsg "fwdURL=$fwdURL"
    # Extract technical filename
    fwdFILE=$(echo $fwdURL | awk -F/ '{print $NF}')
    logMsg "fwdFILE=$fwdFILE"
    # Call download URL and remove lines of response that are not part of the csv file
    curl --no-progress-meter $fwdURL | grep ";" > $DATA_DOWNLOAD_DIR/$dsDIR/$fwdFILE
    RC=$?
    cd $CUR_DIR
    # Check for curl technical error
    if [ $RC -ne 0 ]
    then
        logMsg "Cannot download $dstFILE. Skipping"
        # Indicate SKIP to airflow
        RC=99
    fi
fi

logMsg "Finished $0"
exit $RC
