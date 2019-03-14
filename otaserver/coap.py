"""CoAP management module."""

import os
import asyncio
import logging
import aiocoap.resource as resource

from aiocoap import Context, Message, CONTENT

logger = logging.getLogger("otaserver")


COAP_PORT = 5683


class FirmwareResource(resource.Resource):
    """CoAP resource returning the latest firmware."""

    def __init__(self, controller, timestamp):
        super(FirmwareResource, self).__init__()
        self._controller = controller
        self._timestamp = timestamp

    async def render_get(self, request):
        """Response to CoAP GET request."""
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP GET firmware received from {}".format(remote))

        firmware = self._controller.get_firmware(self._timestamp)
        return Message(code=CONTENT, payload=firmware)


class ManifestResource(resource.Resource):
    """CoAP resource returning the firmware latest version."""

    def __init__(self, controller, timestamp):
        super(ManifestResource, self).__init__()
        self._controller = controller
        self._timestamp = timestamp

    async def render_get(self, request):
        """Response to CoAP GET request."""
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP GET manifest received from {}".format(remote))

        manifest = self._controller.get_manifest(self._timestamp)
        return Message(code=CONTENT, payload=manifest)


class CoapController():
    """CoAP controller with CoAP server inside."""

    def __init__(self, upload_path, port=COAP_PORT):
        self.port = port
        self.upload_path = upload_path
        self.root_coap = resource.Site()
        self.add_resources('latest')
        for timestamp in os.listdir(os.path.join(self.upload_path, 'archived')):
            self.add_resources(timestamp)
        asyncio.async(Context.create_server_context(self.root_coap,
                                                    bind=('::', self.port)))

    def add_resources(self, timestamp):
        """Add new resources for the given timestamp."""
        self.root_coap.add_resource((timestamp, 'firmware',),
                                    FirmwareResource(self, timestamp))
        self.root_coap.add_resource((timestamp, 'manifest',),
                                    ManifestResource(self, timestamp))

    def _store_path(self, timestamp):
        if timestamp == 'latest':
            return os.path.join(self.upload_path, 'latest')
        else:
            return os.path.join(self.upload_path, 'archived', timestamp)

    def get_firmware(self, timestamp):
        """Get firmware content."""
        _firmware_file = os.path.join(self._store_path(timestamp),
                                      'firmware')

        return open(_firmware_file, 'rb').read()

    def get_manifest(self, timestamp):
        """Get manifest content."""
        _manifest_file = os.path.join(self._store_path(timestamp),
                                      'manifest')
        return open(_manifest_file, 'rb').read()
