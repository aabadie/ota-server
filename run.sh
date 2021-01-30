#!/bin/bash

: ${COAP_HOST:=[::1]}
: ${COAP_PORT:=5683}
: ${ROOT_URL:=}

python3 /opt/ota-server/otaserver/main.py \
            --coap-host=${COAP_HOST} --coap-port=${COAP_PORT} \
            --root-url=${ROOT_URL} --debug
