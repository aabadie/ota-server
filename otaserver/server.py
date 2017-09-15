"""Broker application module."""

import os
import os.path
import logging
import tornado
import tornado.platform.asyncio
from tornado.options import options
from tornado import web

from .coap import CoapController
from .firmware import Firmware


logger = logging.getLogger("otaserver")


class OTAServerMainHandler(web.RequestHandler):
    """Web application handler for web page."""

    @web.asynchronous
    def get(self):
        logging.debug("Handling get request received.")
        os.listdir(self.application.upload_path)

        self.render("otaserver.html",
                    favicon=os.path.join("assets", "favicon.ico"),
                    title="OTA Server application",
                    firmwares=self.application.firmwares)


class OTAServerUploadHandler(tornado.web.RequestHandler):
    """Web application handler for firmware post requests."""

    @web.asynchronous
    def post(self):
        files = self.request.files
        if 'slot1' in files and 'slot2' in files:
            filename_slot1 = files['slot1'][0]['filename']
            body_slot1 = files['slot1'][0]['body']

            filename_slot2 = files['slot2'][0]['filename']
            body_slot2 = files['slot2'][0]['body']

            logger.debug("Process files {} and {}".format(filename_slot1,
                                                          filename_slot2))

            logger.debug("Process content {} and {}".format(body_slot1,
                                                            body_slot2))

            for filename, body in [(filename_slot1, body_slot1),
                                   (filename_slot2, body_slot2)]:
                logging.debug("Adding firmware '{}', '{}'."
                              .format(filename, body))

                fname_slot = os.path.join(self.application.upload_path,
                                          filename)

                firmware = Firmware(fname_slot)
                if firmware.check_filename():
                    if not os.path.isfile(fname_slot):
                        with open(fname_slot, 'wb') as file_h:
                            file_h.write(body)
                        self.application.firmwares.append(firmware)
                        self.application.coap_server.add_resources(
                        os.path.basename(fname_slot))
                        logging.debug("New firmware added '{}'."
                                      .format(fname_slot))
                    else:
                        logging.debug("Firmware already exists '{}'."
                                      .format(fname_slot))
                else:
                    logging.debug("Invalid firmware name '{}'."
                                  .format(fname_slot))
        else:
            logger.debug("No valid post request")

        logger.debug("Redirect to main page")
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
                                          port=options.coap_port,
                                          dtls_enabled=options.dtls)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.port))
