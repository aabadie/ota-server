"""Broker application module."""

import os
import os.path
import logging
import json
import datetime
import tornado
import tornado.platform.asyncio
from tornado.options import options
from tornado import web

from coap import CoapController

logger = logging.getLogger("otaserver")


class OTAServerMainHandler(web.RequestHandler):
    """Web application handler for web page."""

    def get(self):
        logging.debug("Handling get request received.")

        self.render("otaserver.html",
                    favicon=os.path.join("assets", "favicon.ico"),
                    title="OTA Server application",
                    firmwares=self.application.firmwares)


class OTAServerFirmwaresHandler(web.RequestHandler):
    """Handler for getting the available firmwares."""

    def get(self):
        pass


class OTAServerPublishHandler(tornado.web.RequestHandler):
    """Handler for publishing new firmwares."""

    def _store_firmware(self, directory, manifest, firmware):
        _store_path = os.path.join(self.application.upload_path, directory)
        if not os.path.exists(_store_path):
            os.makedirs(_store_path)
        _manifest_path = os.path.join(_store_path, 'manifest')
        _firmware_path = os.path.join(_store_path, 'firmware')

        with open(_manifest_path, 'wb') as f:
            f.write(manifest)
        with open(_firmware_path, 'wb') as f:
            f.write(firmware)

    def store_latest(self, manifest, firmware):
        self._store_firmware('latest', manifest, firmware)

    def archive_firmware(self, manifest, firmware):
        timestamp = datetime.datetime.now().strftime('%s')
        _archive_path = os.path.join('archived', timestamp)
        self._store_firmware(_archive_path, manifest, firmware)
        return timestamp

    def post(self):
        files = self.request.files
        if 'manifest' in files and 'firmware' in files:
            manifest_fname = files['manifest'][0]['filename']
            manifest = files['manifest'][0]['body']

            logger.debug('Got manifest file %s', manifest_fname)
            logger.debug('Got manifest body %s', manifest)

            firmware_fname = files['firmware'][0]['filename']
            firmware = files['firmware'][0]['body']

            logger.debug('Got firmware file %s', firmware_fname)
            logger.debug('Got firmware body %s', firmware)

            timestamp = self.archive_firmware(manifest, firmware)
            self.store_latest(manifest, firmware)

            self.application.coap_server.add_resources(timestamp)

        logger.debug("Redirect to main page")
        self.redirect("/")


class OTAServerApplication(web.Application):
    """Tornado based web application providing the OTA server."""

    def __init__(self):
        if options.debug:
            logger.setLevel(logging.DEBUG)

        handlers = [
            (r"/", OTAServerMainHandler),
            (r"/publish", OTAServerPublishHandler),
            (r"/firmwares", OTAServerFirmwaresHandler),
        ]

        self.upload_path = options.upload_path
        self.setup_dirs()
        archived_path = os.path.join(self.upload_path, 'archived')
        self.firmwares = os.listdir(archived_path)

        settings = dict(debug=True,
                        static_path=options.static_path,
                        template_path=options.static_path,
                        )

        self.coap_server = CoapController(self.upload_path,
                                          port=options.coap_port)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.port))

    def setup_dirs(self):
        archived_path = os.path.join(self.upload_path, 'archived')
        if not os.path.exists(archived_path):
            os.makedirs(archived_path)
        latest_path = os.path.join(self.upload_path, 'latest')
        if not os.path.exists(latest_path):
            os.makedirs(latest_path)
