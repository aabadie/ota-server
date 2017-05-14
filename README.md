### OTA Server web application

This application displays the list of available firmwares on the server and
provides a firmware upload mechanism.

#### Installation

OTA Server requires Python 3 (>= 3.4) and can be installed with
[pip](https://github.com/pypa/pip). So you have to install pip for Python 3:
```
    $ wget -qO - https://bootstrap.pypa.io/get-pip.py | sudo python3
```

Once this repository has been cloned:
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

Notes:
* Use `--debug` option if you want more output from the application.
* Use `--coap-port` option to use another port for the CoAP server (5683 is the
  default).
