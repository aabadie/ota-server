"""CoAP test node."""


import os
import os.path
import sys
import asyncio
import logging
import argparse

import aiocoap
import aiocoap.resource as resource
from aiocoap import Context, Message, GET, POST, CHANGED


LOGGER = logging.getLogger("otatestnode")
LOGGER.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)-15s %(levelname)-7s '
                              '%(filename)10s:%(lineno)-3d %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
LOGGER.addHandler(console_handler)

parser = argparse.ArgumentParser(description="Test CoAP client")
parser.add_argument('--resource', type=str, default="notify",
                    help="Device Coap resource.")
parser.add_argument('--port', type=int, default=5683,
                    help="Device Coap server port.")
args = parser.parse_args()

FIRMWARE_PATH = os.path.join(os.path.dirname(__file__), "firmwares")
COAP_PORT = args.port


async def _get_file(url, method=GET, payload=b''):
    protocol = await Context.create_client_context(loop=None)
    request = Message(code=method, payload=payload)
    request.set_request_uri(url)
    try:
        response = await protocol.request(request).response
    except Exception as e:
        code = "Failed to fetch resource"
        payload = '{}'.format(e)
    else:
        code = response.code
        payload = response.payload
    finally:
        await protocol.shutdown()

    LOGGER.debug('{}: {}'.format(code, payload))
    return code, payload


class TriggerResource(resource.Resource):
    """Test node firmware notify resource."""

    def __init__(self):
        super(TriggerResource, self).__init__()

    async def render_post(self, request):
        LOGGER.debug('Update available at {}'.format(request.payload.decode()))
        LOGGER.debug('Fetching manifest')
        await _get_file(request.payload.decode())
        return aiocoap.Message(code=CHANGED, payload=request.payload)


class InactiveResource(resource.Resource):
    """Test node firmware inactive slot resource."""

    def __init__(self):
        super(InactiveResource, self).__init__()
        self.inactive = 0

    async def render_get(self, request):
        LOGGER.debug('Received request on inactive resource')
        self.inactive += 1
        self.inactive %= 2
        return aiocoap.Message(code=CHANGED,
                               payload='{}'.format(self.inactive).encode())


class CoapServer():
    """Coap Server."""

    def __init__(self, port=COAP_PORT):
        self.port = port
        self.root_coap = resource.Site()
        self.root_coap.add_resource(('suit', 'trigger', ),
                                    TriggerResource())
        self.root_coap.add_resource(('suit', 'slot', 'inactive', ),
                                    InactiveResource())
        asyncio.ensure_future(
            Context.create_server_context(self.root_coap,
                                          bind=('::', self.port)))
        LOGGER.debug("CoAP server started, listening on port %s", COAP_PORT)


if __name__ == '__main__':
    try:
        ioloop = asyncio.get_event_loop()
        # Aiocoap server initialization
        coap_server = CoapServer(COAP_PORT)

        # Loop forever
        ioloop.run_forever()

    except KeyboardInterrupt:
        print("Exiting")
        ioloop.stop()
        sys.exit()