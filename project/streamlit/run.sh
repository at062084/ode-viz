#!/usr/bin/bash

IMG_REG="localhost/ode-streamlit:latest"
IMG_NAME="ode-streamlit"
VOL_POD_DATA="/export/data"
VOL_IMG_DATA="/export/data"
PORT_POD_ST="8501"
PORT_IMG_ST="8501"
PORT_POD_DTALE="40000"
PORT_IMG_DTALE="40000"


podman run --rm --detach --replace --pull newer --tls-verify=false \
        --privileged \
        --name $IMG_NAME \
        --volume $VOL_POD_DATA:$VOL_IMG_DATA \
        --publish $PORT_POD_ST:$PORT_IMG_ST \
        --publish $PORT_POD_DTALE:$PORT_IMG_DTALE \
        --env DATA_ROOT_DIR=$VOL_IMG_DATA \
        $IMG_REG
