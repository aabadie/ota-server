"""CoAP management module."""

import os
import asyncio
import logging
import aiocoap.resource as resource

from aiocoap import Context, Message, CONTENT

logger = logging.getLogger("otaserver")


COAP_PORT = 5683


class FirmwareBinaryResource(resource.Resource):
    """CoAP resource returning the latest firmware."""

    def __init__(self, controller):
        super(FirmwareBinaryResource, self).__init__()
        self._controller = controller

    @asyncio.coroutine
    def render_get(self, request):
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP GET received from {}".format(remote))

        fw = self._controller.get_latest_firmware()

        return Message(
            code=CONTENT,
            payload=fw)


class FirmwareVersionResource(resource.Resource):
    """CoAP resource returning the firmware latest version."""

    def __init__(self, controller):
        super(FirmwareVersionResource, self).__init__()
        self._controller = controller

    @asyncio.coroutine
    def render_get(self, request):
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP GET received from {}".format(remote))

        return Message(
            code=CONTENT,
            payload=self._controller.get_latest_version().encode('ascii'))


class CoapController():
    """CoAP controller with CoAP server inside."""

    def __init__(self, fw_path, port=COAP_PORT):
        self.port = port
        self.fw_path = fw_path
        root_coap = resource.Site()
        root_coap.add_resource(('version', ), FirmwareVersionResource(self))
        root_coap.add_resource(('firmware', ), FirmwareBinaryResource(self))
        asyncio.async(Context.create_server_context(root_coap,
                                                    bind=('::', self.port)))

    def get_latest_version(self):
        """Get the latest firmware version."""
        firmwares = os.listdir(self.fw_path)
        if firmwares == []:
            return ''
        else:
            return '.'.join(max(os.path.splitext(
                fw)[0].split("-")[-1].split(".") for fw in firmwares))

    def get_latest_firmware(self):
        """Get the latest firmware content."""
        firmwares = os.listdir(self.fw_path)
        latest_version = self.get_latest_version()
        firmware = [fw for fw in firmwares
                    if os.path.splitext(fw)[0].endswith(latest_version)][0]
        return open(os.path.join(self.fw_path, firmware), 'rb').read()
