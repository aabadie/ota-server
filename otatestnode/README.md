### OTA Coap Device Test Server ###

This application creates a coap server that exposes a resource where it can be notified
of firmware updates. Default is '/notify'. It receives as paylaod a URL where to fetch the
manifest.

Once it receives the URL it makes a GET request to the provided URL and retrieves the manifest.

#### Run the server

Starting the server is as simple as:

    $ python otatestnode/coap_node.py

Notes:

- Use `--resource` option to specify the naem of the resource to expose 
  (default is '/notify')
- Use `--port` option to use another port for the CoAP server (5683 is the
  default)