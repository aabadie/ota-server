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


class OTAServerPublishHandler(tornado.web.RequestHandler):
    """Handler for publishing new firmwares."""

    def _store(self, store_url, manifest, slot0, slot1):
        _store_path = os.path.join(self.application.upload_path, store_url)
        if not os.path.exists(_store_path):
            os.makedirs(_store_path)
        _manifest_path = os.path.join(_store_path, 'manifest')
        _slot0_path = os.path.join(_store_path, 'slot0')
        _slot1_path = os.path.join(_store_path, 'slot1')

        with open(_manifest_path, 'wb') as f:
            f.write(manifest)
        with open(_slot0_path, 'wb') as f:
            f.write(slot0)
        with open(_slot1_path, 'wb') as f:
            f.write(slot1)

    def post(self):
        files = self.request.files
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        # Cleanup the path
        store_path = publish_id.replace('/', '_').replace('\\', '_')
        node_url = self.request.body_arguments['node_url'][0].decode()

        logger.debug('Storing new firmware in %s', publish_id)
        logger.debug('Publish new firmware to %s', node_url)
        msg = None
        for resource in ('manifest', 'slot0', 'slot1'):
            if resource not in files:
                msg = "Missing {} file".format(resource)
        if msg is not None:
            self.set_status(400, msg)
            self.finish(msg)
            return

        manifest = files['manifest'][0]['body']
        slot0 = files['slot0'][0]['body']
        slot1 = files['slot0'][0]['body']

        self._store(store_path, manifest, slot0, slot1)
        self.application.coap_server.add_resources(store_path)

        # logger.debug("Redirect to main page")
        # self.redirect("/")


class OTAServerApplication(web.Application):
    """Tornado based web application providing the OTA server."""

    def __init__(self):
        if options.debug:
            logger.setLevel(logging.DEBUG)

        handlers = [
            (r"/", OTAServerMainHandler),
            (r"/publish", OTAServerPublishHandler),
        ]

        self.upload_path = options.upload_path
        self.firmwares = os.listdir(self.upload_path)

        settings = dict(debug=True,
                        static_path=options.static_path,
                        template_path=options.static_path,)

        self.coap_server = CoapController(self.upload_path,
                                          port=options.coap_port)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.port))
