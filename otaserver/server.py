"""Broker application module."""

import os
import os.path
import logging
import json
import datetime
import asyncio
import tornado
import tornado.platform.asyncio
from tornado.options import options
from tornado import web

from coap import CoapServer, coap_notify, COAP_METHOD

logger = logging.getLogger("otaserver")


def _path_from_publish_id(publish_id):
    _path = publish_id.replace('/', '_').replace('\\', '_')
    return _path


class OTAServerMainHandler(web.RequestHandler):
    """Web application handler for web page."""

    def get(self):
        logging.debug("Handling get request received.")

        self.render("otaserver.html",
                    favicon=os.path.join("assets", "favicon.ico"),
                    title="OTA Server application",
                    firmwares=self.application.firmwares)


class OTAServerNotifyHandler(tornado.web.RequestHandler):
    """Handler for notifying an update to a list of devices."""

    def post(self):
        """Handle notification of an available update."""
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        publish_path = _path_from_publish_id(publish_id)

        manifest_url = os.path.join(publish_path, 'manifest')
        manifest_store_path = os.path.join(self.application.upload_path,
                                           manifest_url)
        if not os.path.isfile(manifest_store_path):
            msg = ("Manifest is not available for publish id {}."
                   .format(publish_id))
            self.set_status(400, msg)
            self.finish(msg)
            return

        devices_urls = self.request.body_arguments['urls'][0].decode()
        logger.debug('Notifying devices %s of an update of %s',
                     devices_urls, publish_id)

        payload = '{}://[{}]:{}/{}'.format(
            COAP_METHOD, options.coap_host, options.coap_port, manifest_url)
        logger.debug('Manifest url is %s', payload)
        for url in devices_urls.split(','):
            logger.debug('Send update notification at %s', url)
            asyncio.ensure_future(coap_notify(url, payload=payload.encode()))


class OTAServerPublishHandler(tornado.web.RequestHandler):
    """Handler for storing published firmwares."""

    def _store(self, store_url, data):
        _store_path = os.path.join(self.application.upload_path, store_url)
        if not os.path.exists(_store_path):
            os.makedirs(_store_path)

        # Store each data in separate files
        for name, content in data.items():
            _path = os.path.join(_store_path, name)
            with open(_path, 'wb') as f:
                f.write(content)

    def post(self):
        """Handle publication of an update."""
        # Verify the request contains the required files
        files = self.request.files
        msg = None
        if len(files) == 0:
            msg = "No file found in request"
        if msg is not None:
            self.set_status(400, msg)
            self.finish(msg)
            return

        # Load the content of the files from the request
        update_data = {}
        for file in files:
            update_data[os.path.basename(file)] = files[file][0]['body']

        # Get publish identifier
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        # Cleanup the path
        store_path = _path_from_publish_id(publish_id)
        logger.debug('Storing %s update in %s', publish_id, store_path)

        # Store the data and create the corresponding CoAP resources
        self._store(store_path, update_data)
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
            (r"/notify", OTAServerNotifyHandler),
        ]

        self.upload_path = options.upload_path
        self.firmwares = os.listdir(self.upload_path)

        settings = dict(debug=True,
                        static_path=options.static_path,
                        template_path=options.static_path,)

        self.coap_server = CoapServer(self.upload_path, port=options.coap_port)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.http_port))
