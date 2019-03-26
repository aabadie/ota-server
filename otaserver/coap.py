"""CoAP management module."""

import os
import asyncio
import logging
import mimetypes
import aiocoap
import aiocoap.resource as resource

from aiocoap import Context, Message, CONTENT, NOT_FOUND, POST

logger = logging.getLogger("otaserver")


COAP_METHOD = 'coap'
COAP_PORT = 5683
COAP_HOST = '[::1]'


def _remote_address(request):
    try:
        remote = request.remote[0]
    except TypeError:
        remote = request.remote.sockaddr[0]
    return remote


class FileResource(resource.Resource):
    """CoAP resource returning the content of a binary file."""

    def __init__(self, controller, file_path):
        super(FileResource, self).__init__()
        self._controller = controller
        self._file_path = file_path

    async def needs_blockwise_assembly(self, request):
        return False

    async def render_get(self, request):
        """Response to CoAP GET request."""
        remote = _remote_address(request)
        logger.debug("CoAP GET manifest received from {}".format(remote))
        if not os.path.isfile(self._file_path):
            err_msg = "File {} not found on server".format(
                self._file_path).encode()
            return Message(code=NOT_FOUND, payload=err_msg)

        block_in = request.opt.block2 or \
            aiocoap.optiontypes.BlockOption.BlockwiseTuple(0, 0, 6)
        
        with open(self._file_path, 'rb') as f:
            f.seek(block_in.start)
            data = f.read(block_in.size + 1)

        block_out = aiocoap.optiontypes.BlockOption.BlockwiseTuple(
            block_in.block_number,
            len(data) > block_in.size,
            block_in.size_exponent)

        return aiocoap.Message(payload=data[:block_in.size], block2=block_out)


class CoapServer():
    """CoAP server."""

    def __init__(self, upload_path, port=COAP_PORT):
        self.root_coap = resource.Site()
        self.port = port
        self.upload_path = upload_path
        self._bootstrap_resources()
        asyncio.ensure_future(Context.create_server_context(self.root_coap,
                              bind=('::', self.port)))

    def _bootstrap_resources(self):
        for version in os.listdir(os.path.join(self.upload_path)):
            self.add_resources(version)

    def add_resources(self, store_path):
        """Add new resources for the given timestamp."""
        for file in os.listdir(os.path.join(self.upload_path, store_path)):
            self.add_resource(store_path, file)

    def add_resource(self, store_path, resource):
        _resource_url = [store_path, resource,]
        _resource_file = os.path.join(self.upload_path, store_path, resource)
        self.root_coap.add_resource(_resource_url,
                                    FileResource(self, _resource_file))


async def coap_request(url, method=POST, payload=b''):
    """Send a CoAP request containing an update notification."""
    logger.debug('Sending a CoAP request to url: {}'.format(url))
    context = await Context.create_client_context(loop=None)
    request = Message(code=method, payload=payload)
    request_uri = '{}://{}'.format(COAP_METHOD, url)
    request.set_request_uri(request_uri)
    try:
        response = await context.request(request).response
    except Exception as e:
        code = "Failed to fetch resource"
        payload = '{}'.format(e)
    else:
        code = response.code
        payload = response.payload.decode('utf-8')
    finally:
        await context.shutdown()

    logger.debug('{}: {}'.format(code, payload))
    return code, payload
