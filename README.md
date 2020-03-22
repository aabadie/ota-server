### OTA Server web application

This application displays the list of available firmwares on the server and
provides a firmware upload mechanism.

#### Installation

OTA Server requires Python 3 (>= 3.5).
All requirements can be installed with [pip](https://github.com/pypa/pip).

1. Install pip for Python 3 using:

    $ wget -qO - https://bootstrap.pypa.io/get-pip.py | sudo python3

2. Then clone this repository:

    $ git clone https://github.com/aabadie/ota-server.git

3. Install the OTA server dependencies:

    $ cd ota-server
    $ sudo pip install -r requirements.txt

#### Run the server

Starting the server is as simple as:

    $ python otaserver/main.py

Notes:

- Use `--debug` option if you want more output from the application.
- Use `--coap-host` option to specify the CoAP server IP that will be used by
  the devices to fetch the files (`::1` is the default)
- Use `--coap-port` option to use another port for the CoAP server (5683 is the
  default)
- Use `--http-port` option to use another port for the HTTP server listening
  to incoming user updates (8080 is the default)
- Use `--help` to get the full list options

#### Run with Docker

The HTTP port and CoAP port have to be explictly exposed to the host when
running the aabadie/ota-server container.
Internally, the HTTP port is 8080 and is fixed. The CoAP is 5683/udp but it can
be changed to a different value using the `COAP_PORT` environment variable.
To set the CoAP host option of the ota-server, use the `COAP_HOST` environment
variable.

Example:
Required setup:
- CoAP host: fd00:dead:beef::1
- CoAP port: 5684/udp
- HTTP port: 8888

Launch the OTA server:
```
docker run --rm -ti -p 8888:8080 -p 5684:5684/udp --env COAP_HOST=[fd00:dead:beef::1] --env COAP_PORT=5684 aabadie/ota-server
```

You can verify that the web interface is available at http://localhost:8888
You can also verify that the CoAP server can be reached using aiocoap:
```
aiocoap-client -m GET coap://[fd00:dead:beef::1]:5684/.well-known/core
```

#### Publish and notify a new version

A new firmware version must provide 3 files:
- a manifest, preferably compliant with SUIT standard
- 2 firmwares, one for slot0 on the flash, one for slot1

2 other information are required:
- the publish id used to identify a set of files on the server
- the device notification url to notify a device that a new version manifest is
  available


Use the provided python client to publish and notify updates:
- publish new files:

      $ python client/otaclient.py --publish-id <publish_id> --files <file1> <file2>

- notify an update to a list of device:

      $ python client/otaclient.py --publish-id <publish_id> --notify <device-ip>/url <other-device-ip>/url2

- combine the previous commands to perform all 3 actions in one call.

All 3 previous actions can also be done using the `curl` command line tool:

- publish new files:

      $ curl -X POST -F 'publish_id=<publish-id>' -F 'file1=@<path to file 1>'
          -F 'file2=@<path to file 2>' http://<server address>:8080/publish

- notify an update to a list of device:

      $ curl -X POST -F 'publish_id=<publish-id>' -F 'urls=<device-ip/>url,<other-device-ip/>url2' http://<server-address>:8080/notify

#### Fetch the available manifest and firmware slots:

Each files of new version can be retrieved under the `<publish_id>` endpoint on
the CoAP server:

- `<publish_id>/manifest`
- `<publish_id>/file1`
- `<publish_id>/file2`

To get the version of the latest firmware available, use a CoAP client on
the corresponding resource. Example with [libcoap]():

    $ coap-client -m get coap://[server ip]/<publish_id>/manifest
    v:1 t:CON c:GET i:9236 {} [ ]
    <content of the manifest>
    $ coap-client -m get coap://[server ip]/<publish_id>/file1
    v:1 t:CON c:GET i:9236 {} [ ]
    <content of file1>
    $ coap-client -m get coap://[server ip]/<publish_id>/file2
    v:1 t:CON c:GET i:9236 {} [ ]
    <content of file2>
