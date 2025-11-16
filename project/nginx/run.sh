#!/usr/bin/bash

IMAGE="nginxproxy/nginx-proxy:1.7.0"
NAME="nginx"
NETWORK="proxynet"
HTTP_PORT=80
HTTPS_PORT=443

echo ""
echo "Executing $0 as $(id -u -n) in `pwd`"

echo "Pulling image $IMAGE"
docker pull $IMAGE

echo "Creating network $NETWORK"
docker network create $NETWORK || true

echo "Running $NAME on HTTP_PORT=$HTTP_PORT and HTTPS_PORT=$HTTPS_PORT"
docker run --rm --detach \
    --name $NAME \
    --publish $HTTP_PORT:$HTTP_PORT \
    --publish $HTTPS_PORT:$HTTPS_PORT \
    --env HTTP_PORT=$HTTP_PORT \
    --env HTTPS_PORT=$HTTPS_PORT \
    --volume /etc/ssl/certs:/etc/nginx/certs:ro \
    --volume /export/log/nginx/proxy.access.log:/var/log/nginx/access.log \
    --volume /export/log/nginx/proxy.error.log:/var/log/nginx/error.log \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --network=$NETWORK \
    $IMAGE

echo "Done"
