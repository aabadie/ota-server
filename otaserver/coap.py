"""CoAP management module."""

import os
import asyncio
import logging
import aiocoap.resource as resource

from aiocoap import Context, Message, CONTENT

logger = logging.getLogger("otaserver")


COAP_PORT = 5683


class FileResource(resource.Resource):
    """CoAP resource returning the content of a binary file."""

    def __init__(self, controller, file_path):
        super(FileResource, self).__init__()
        self._controller = controller
        self._file_path = file_path

    async def render_get(self, request):
        """Response to CoAP GET request."""
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP GET manifest received from {}".format(remote))
        payload = open(self._file_path, 'rb').read()
        return Message(code=CONTENT, payload=payload)


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
        for resource in ('manifest', 'slot0', 'slot1'):
            self.add_resource(store_path, resource)

    def add_resource(self, store_path, resource):
        _resource_url = [store_path, resource,]
        _resource_file = os.path.join(self.upload_path, store_path, resource)
        self.root_coap.add_resource(_resource_url,
                                    FileResource(self, _resource_file))
