"""CoAP test node."""


import os
import os.path
import sys
import asyncio
import logging
import argparse

import tornado.platform.asyncio
from tornado import gen
from tornado.ioloop import PeriodicCallback

import aiocoap
import aiocoap.resource as resource
from aiocoap import Context, Message, GET, POST

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)14s - '
                           '%(levelname)5s - %(message)s')
logger = logging.getLogger("tornado.internal")

parser = argparse.ArgumentParser(description="Test CoAP client")
parser.add_argument('--host', type=str, default="localhost",
                    help="Device Coap server host.")
parser.add_argument('--port', type=int, default=5683,
                    help="Device Coap server port.")
args = parser.parse_args()

FIRMWARE_PATH = os.path.join(os.path.dirname(__file__), "firmwares")
COAP_PORT = args.port


async def _get_firmware(url, method=GET, payload=b''):
    protocol = await Context.create_client_context(loop=None)
    request = Message(code=method, payload=payload)
    request.set_request_uri(url)
    try:
        response = await protocol.request(request).response
    except Exception as e:
        code = "Failed to fetch resource"
        payload = '{0}'.format(e)
    else:
        code = response.code
        payload = response.payload.decode('utf-8')
    finally:
        await protocol.shutdown()

    logger.debug('Code: {0} - Payload: {1}'.format(code, payload))
    return code, payload

class NotifyResource(resource.Resource):
    """Test node firmware notify resource."""

    def __init__(self):
        super(NotifyResource, self).__init__()

    def _store_firmware(self, filename, firmware):
        _store_path = FIRMWARE_PATH
        if not os.path.exists(_store_path):
            os.makedirs(_store_path)
        _firmware_file_path = os.path.join(_store_path, filename)

        with open(_firmware_file_path, 'wb') as f:
            f.write(firmware.encode('utf-8'))

    async def _get_new_firmwares(self, update_path):
        logger.debug('New firmware update available at %s', update_path)
        _, manifest = await _get_firmware(update_path.decode('utf-8'))
        self._store_firmware('manifest', manifest)

    async def render_put(self, request):
        logger.debug('Code: {0} - Payload: {1}'.format(request.code,
                    request.payload))
        await self._get_new_firmwares(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED,
                               payload=request.payload)

class CoapServer():
    """Coap Server."""

    def __init__(self, port=COAP_PORT):
        self.port = port
        self.root_coap = resource.Site()
        self.setup_resources()
        asyncio.ensure_future(Context.create_server_context(self.root_coap,
                                                    bind=('::', self.port)))

    def setup_resources(self):
        """Set up controller resources."""
        self.root_coap.add_resource(('notify', ), NotifyResource())
        self.root_coap.add_resource(('.well-known', 'core'),
                          resource.WKCResource(
                              self.root_coap.get_resources_as_linkheader))

if __name__ == '__main__':
    try:
        # Tornado ioloop initialization
        ioloop = asyncio.get_event_loop()
        tornado.platform.asyncio.AsyncIOMainLoop().install()

        # Aiocoap server initialization
        coap_server = CoapServer(COAP_PORT)

        # Loop forever
        ioloop.run_forever()

    except KeyboardInterrupt:
        print("Exiting")
        ioloop.stop()
        sys.exit()