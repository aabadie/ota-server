"""Broker application module."""

import os
import os.path
import logging
import tornado
from tornado.options import options
from tornado import web
import tornado.platform.asyncio

from .coap import CoapController
from .firmware import Firmware


logger = logging.getLogger("otaserver")


class OTAServerMainHandler(web.RequestHandler):
    """Web application handler for web page."""

    @tornado.web.asynchronous
    def get(self):
        logging.debug("Handling get request received.")
        os.listdir(self.application.upload_path)

        self.render("otaserver.html",
                    favicon=os.path.join(options.static_path,
                                         "assets", "favicon.ico"),
                    title="OTA Server application",
                    firmwares=self.application.firmwares)


class OTAServerUploadHandler(tornado.web.RequestHandler):
    """Web application handler for firmware post requests."""

    @tornado.web.asynchronous
    def post(self):
        if (hasattr(self.request.files, 'slot1') and
                hasattr(self.request.files, 'slot2')):
            fileinfo_slot1 = self.request.files['slot1'][0]
            fileinfo_slot2 = self.request.files['slot2'][0]

            logger.debug("Got files {} and {}"
                        .format(fileinfo_slot1, fileinfo_slot2))

            self.application.add_firmware(fileinfo_slot1)
            self.application.add_firmware(fileinfo_slot2)
        else:
            logger.debug("No valid post request")

        self.redirect("/")


class OTAServerApplication(web.Application):
    """Tornado based web application providing the OTA server."""

    def __init__(self):
        if options.debug:
            logger.setLevel(logging.DEBUG)

        handlers = [
            (r"/", OTAServerMainHandler),
            (r"/upload", OTAServerUploadHandler),
        ]

        self.upload_path = options.upload_path
        self.firmwares = [Firmware(os.path.join(self.upload_path, fname))
                          for fname in os.listdir(self.upload_path)]

        settings = dict(debug=True,
                        static_path=options.static_path,
                        template_path=options.static_path,
                        )
        self.coap_server = CoapController(os.path.join(options.static_path,
                                                       "uploads"),
                                          port=options.coap_port)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.port))

    def add_firmware(self, slot):
        """Add firmware to web application."""
        # Only manage upload if firmware filename is valid
        fname_slot = os.path.join(self.upload_path, slot['filename'])
        body_slot = slot["body"]

        firmware_slot = Firmware(fname_slot)
        if firmware_slot.check_filename():
            if not os.path.isfile(fname_slot):
                with open(firmware_slot.filename(), 'wb') as file_h:
                    file_h.write(body_slot)
                self.firmwares.append(firmware_slot)
                self.coap_server.add_resources(
                    os.path.basename(fname_slot))
                logging.debug("New firmware {}.".format(fname_slot))