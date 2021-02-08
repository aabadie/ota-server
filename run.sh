#!/bin/bash

: ${COAP_HOST:=[::1]}
: ${COAP_PORT:=5683}
: ${HTTP_HOST:=localhost}
: ${HTTP_PORT:=8080}
: ${ROOT_URL:=}
: ${NOTIFY_URL:="suit/trigger"}

python3 /opt/ota-server/otaserver/main.py \
            --coap-host=${COAP_HOST} --coap-port=${COAP_PORT} \
            --http-host=${HTTP_HOST} --http-port=${HTTP_PORT} \
            --root-url=${ROOT_URL} --notify-url ${NOTIFY_URL} \
            --debug
