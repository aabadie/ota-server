#!/bin/bash

: ${COAP_HOST:=[::1]}
: ${COAP_PORT:=5683}

python3 /opt/ota-server/otaserver/main.py \
            --coap-host=${COAP_HOST} --coap-port=${COAP_PORT} \
            --http-port=8080 \
            --debug
