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
parser.add_argument('--gateway-host', type=str, default="localhost",
                    help="Gateway Coap server host.")
parser.add_argument('--gateway-port', type=int, default=5683,
                    help="Gateway Coap server port.")
args = parser.parse_args()

FIRMWARE_PATH = os.path.join(os.path.dirname(__file__), "firmwares")
DEVICE_URL = 'coap://{}:{}'.format(args.gateway_host, args.gateway_port)
COAP_PORT = args.gateway_port


@asyncio.coroutine
def _coap_resource(url, method=GET, payload=b''):
    protocol = yield from Context.create_client_context(loop=None)
    request = Message(code=method, payload=payload)
    request.set_request_uri(url)
    try:
        response = yield from protocol.request(request).response
    except Exception as e:
        code = "Failed to fetch resource"
        payload = '{0}'.format(e)
    else:
        code = response.code
        payload = response.payload.decode('utf-8')
    finally:
        yield from protocol.shutdown()

    logger.debug('Code: {0} - Payload: {1}'.format(code, payload))

    return code, payload

@gen.coroutine
def _get_firmware(url, firmware):
    code, payload = yield from _coap_resource('{}/{}'.format(url,firmware),
                                     method=GET)

class UpdateResource(resource.Resource):
    """Test node firmware update resource."""

    def __init__(self, controller):
        super(UpdateResource, self).__init__()
        self._controller = controller

    def set_update_url(self, url):
        self._controller.update_path.data = url

    async def render_get(self, request):
        return aiocoap.Message(payload=self._controller.update_path.data)

    async def render_put(self, request):
        logger.debug('Code: {0} - Payload: {1}'.format(request.code,
                    request.payload))
        self.set_update_url(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED,
                               payload=self._controller.update_path.data)

class ObservedData(object):
    """Data object that can notify and execute callbacks upon changes."""
    def __init__(self, value):
        self._data = value
        self._observers = []

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        for callback in self._observers:
            callback()

    def bind_to(self, callback):
        self._observers.append(callback)

class UpdateController(object):
    """Update controller with CoAP server inside."""

    def __init__(self, update_path, port=COAP_PORT):
        self.port = port
        self.update_path = ObservedData(update_path)
        self.update_path.bind_to(self._get_new_firmwares)
        self.root_coap = resource.Site()
        self.setup_resources()

        asyncio.async(Context.create_server_context(self.root_coap,
                                                    bind=('::', self.port)))

    def setup_resources(self):
        """Set up controller resources."""
        self.root_coap.add_resource(('updates', ), UpdateResource(self))
        self.root_coap.add_resource(('.well-known', 'core'),
                          resource.WKCResource(
                              self.root_coap.get_resources_as_linkheader))

    def _store_firmware(self, filename, firmware):
        _store_path = os.path.join(FIRMWARE_PATH)
        if not os.path.exists(_store_path):
            os.makedirs(_store_path)
        _firmware_path = os.path.join(_store_path, filename)

        with open(_firmware_path, 'wb') as f:
            f.write(firmware)

    def _get_new_firmwares(self):
        logger.debug('New firmware update available Url %s',
                      self.update_path.data)
        # Fetch new Firmware
        _, manifest await _get_firmware(self.update_path.data, 'manifest')
        _, slot0 await _get_firmware(self.update_path.data, 'slot0')
        _, slot1 await _get_firmware(self.update_path.data, 'slot1')
        # Store new firmware
        self._store_firmware('manifest', manifest)
        self._store_firmware('slot0', slot0)
        self._store_firmware('slot1', slot1)


if __name__ == '__main__':
    try:
        # Tornado ioloop initialization
        ioloop = asyncio.get_event_loop()
        tornado.platform.asyncio.AsyncIOMainLoop().install()

        # Aiocoap server initialization
        coap_server = UpdateController("adsfasd",
                                          port=args.gateway_port)

        asyncio.async(aiocoap.Context.create_server_context(coap_server.root_coap))

        # Loop forever
        ioloop.run_forever()

    except KeyboardInterrupt:
        print("Exiting")
        ioloop.stop()
        sys.exit()