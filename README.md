### OTA Server web application

This application displays the list of available firmwares on the server and
provides a firmware upload mechanism.

#### Installation

OTA Server requires Python 3 (>= 3.4) and can be installed with
[pip](https://github.com/pypa/pip). So you have to install pip for Python 3:
```
    $ wget -qO - https://bootstrap.pypa.io/get-pip.py | sudo python3
```

First clone this repository:
```
    $ git clone https://github.com/aabadie/ota-server.git
```

Then install OTA server:
```
    $ cd ota-server
    $ sudo pip install .
```

Finally install the Node modules required (you need to install
[npm](https://www.npmjs.com/get-npm) first):
```
    $ cd ota-server/otaserver/static
    $ npm install
```

#### Running the server

Start the server using `--static-path` to indicate where the html and css files
are located. They should normally be in `ota-server/ota-server/static` if you
followed the installation steps:
```
    $ ota-server --static-path=<ota-server>/otaserver/static
```

The web application is available at http://localhost:8080

Notes:
* Use `--debug` option if you want more output from the application.
* Use `--coap-port` option to use another port for the CoAP server (5683 is the
  default).

#### About the available firmwares:

The firmwares name should match the following pattern:
```
<filename>-<major version>.<minor version>.<patch version>.elf
```
Any file uploaded that doesn't match this pattern is ignored.

The uploaded firmwares are uploaded in the following directory:
`<ota-server>/otaserver/static/uploads`

To get the version of the latest firmware available, use a CoAP client on
`version` resource. Example with [libcoap]():
```
coap-client -m get coap://[server ip]/version
v:1 t:CON c:GET i:9236 {} [ ]
1.0.2
```
