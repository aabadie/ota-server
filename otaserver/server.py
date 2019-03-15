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

    def put(self):
        """Handle notification of an available update."""
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        publish_path = publish_id.replace('/', '_').replace('\\', '_')

        manifest_url = os.path.join(publish_path, 'manifest')
        devices_urls = self.request.body_arguments['device_urls'][0].decode()
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
        for resource in ('manifest', 'slot0', 'slot1'):
            if resource not in files:
                msg = "Missing {} file".format(resource)
        if msg is not None:
            self.set_status(400, msg)
            self.finish(msg)
            return

        # Load the content of the files from the request
        manifest = files['manifest'][0]['body']
        slot0 = files['slot0'][0]['body']
        slot1 = files['slot0'][0]['body']
        update_data = {'manifest': manifest, 'slot0': slot0, 'slot1': slot1}

        # Get publish identifier
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        # Cleanup the path
        store_path = publish_id.replace('/', '_').replace('\\', '_')
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
