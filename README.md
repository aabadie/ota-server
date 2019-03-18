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
- Use `--coap-port` option to use another port for the CoAP server (5683 is the
  default)
- Use `--http-port` option to use another port for the HTTP server listening
  to incoming user updates (8080 is the default)
- Use `--help` to get the full list options

#### Publish and notify a new version

A new firmware version must provide 3 files:
- a manifest, preferably compliant with SUIT standard
- 2 firmwares, one for slot0 on the flash, one for slot1

2 other information are required:
- the publish id used to identify a set of files on the server
- the device notification url to notify a device that a new version manifest is
  available

Use the otaclient tool to publish new files:

    $ python client/otaclient.py --publish-id <publish_id> --publish <file1> <file2>

Use the otaclient tool to publish the manifest corresponding to these files:

    $ python client/otaclient.py --publish-id <publish_id> --manifest <manifest.bin>

Use the otaclient tool to notify an update:

    $ python client/otaclient.py --publish-id <publish_id> --notify <device-ip>/url <other-device-ip>/url2

All commands can be combined in a single one to:
- publish different image files
- publish a new manifest
- notify a list of device

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
