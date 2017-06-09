"""CoAP management module."""

import os
import asyncio
import logging
import aiocoap.resource as resource

from aiocoap import Context, Message, CONTENT
from functools import reduce

logger = logging.getLogger("otaserver")
COAP_PORT = 5678

class FirmwareUpdate(object):
    """Firmware updates as files."""
    def __init__(self, fw_name):
        self.slot = os.path.splitext(fw_name.split("-")[-3])
        self.appid = os.path.splitext(fw_name.split("-")[-2])
        self.version = os.path.splitext(fw_name.split("-")[-1])
        self.name = fw_name

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

    def __init__(self, controller, appid):
        super(FirmwareVersionResource, self).__init__()
        self._controller = controller
        self.appid = appid

    @asyncio.coroutine
    def render_get(self, request):
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP GET received from {}".format(remote))
        message = self._controller.get_latest_version(self.appid).encode('ascii')
        logger.debug("Sending message: {}".format(message))

        return Message(
            code=CONTENT,
            payload=message)

class FirmwareNameResource(resource.Resource):
    """CoAP resource returning the firmware name of latest version."""

    def __init__(self, controller, appid, slot):
        super(FirmwareNameResource, self).__init__()
        self._controller = controller
        self.appid = appid
        self.slot = slot

    @asyncio.coroutine
    def render_get(self, request):
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP GET received from {}".format(remote))
        message = self._controller.get_latest_fw_name(self.appid, self.slot).encode('ascii')
        logger.debug("Sending message: {}".format(message))

        return Message(
            code=CONTENT,
            payload=message)


class CoapController():
    """CoAP controller with CoAP server inside."""

    def __init__(self, fw_path, port=COAP_PORT):
        self.port = port
        self.fw_path = fw_path
        root_coap = resource.Site()
        self.appids = {}
        firmwares = os.listdir(self.fw_path)
        for fw in firmwares:
            firmware = FirmwareUpdate(fw)
            appid = fw.split("-")[-2]
            if appid in self.appids:
                self.appids[appid].append(fw)
                continue
            self.appids[appid] = [fw]
            print (appid)
            root_coap.add_resource((appid, 'version', ), FirmwareVersionResource(self, appid))
            root_coap.add_resource((appid, 'slot1', 'name', ), FirmwareNameResource(self, appid, 1))
            root_coap.add_resource((appid, 'slot2', 'name', ), FirmwareNameResource(self, appid, 2))
        
        asyncio.async(Context.create_server_context(root_coap,
                                                    bind=('::', self.port)))

    def get_latest_version(self, appid):
        """Get the latest firmware version."""
        firmwares = os.listdir(self.fw_path)
        if firmwares == []:
            return ''
        else:
            fw_appids = list(filter(lambda x: x.split("-")[-2] == appid, firmwares))
            return max([fw.split("-")[-1] for fw in fw_appids])

    def get_latest_fw_name(self, appid, slot):
        """Get the latest firmware name."""
        firmwares = os.listdir(self.fw_path)
        if firmwares == []:
            return ''
        else:
            version = self.get_latest_version(appid)
            fw_appids = list(filter(lambda x: x.split("-")[-2] == appid and x.split("-")[-1] == version, firmwares))
            print (fw_appids)
            fw_name = list(filter(lambda x: x.split("-")[-3] == 'slot' + str(slot), fw_appids))
            print (fw_name)
            return fw_name[0]

    def get_latest_firmware(self):
        """Get the latest firmware content."""
        latest_version = self.get_latest_version()
        firmware = [fw for fw in self.firmwares
                    if os.path.splitext(fw)[0].endswith(latest_version)][0]
        return open(os.path.join(self.fw_path, firmware), 'rb').read()
