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

from aiocoap import GET

from coap import CoapServer, coap_request, COAP_METHOD

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


class OTAServerCoapUrlHandler(web.RequestHandler):
    """Web application handler for getting the CoAP url."""

    async def get(self):
        _coap_uri = 'coap://{}:{}'.format(options.coap_host, options.coap_port)
        _publish_id = self.request.path.split('/')[-1]
        _coap_url = '{}/{}'.format(_coap_uri, _publish_id)
        logger.debug("Sending CoAP server url: %s", _coap_url)
        self.write(_coap_url)


class OTAServerNotifyHandler(tornado.web.RequestHandler):
    """Handler for notifying an update to a list of devices."""

    async def post(self):
        """Handle notification of an available update."""
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        publish_path = _path_from_publish_id(publish_id)

        _store_path = os.path.join(self.application.upload_path, publish_id)
        base_filename = os.listdir(_store_path)[0].split('-')[0]

        slot0_manifest_url = os.path.join(
            publish_path,
            '{}-slot0.riot.suit.latest.bin'.format(base_filename))
        slot1_manifest_url = os.path.join(
            publish_path,
            '{}-slot1.riot.suit.latest.bin'.format(base_filename))

        devices_urls = self.request.body_arguments['urls'][0].decode()
        logger.debug('Notifying devices %s of an update of %s',
                     devices_urls, publish_id)

        for url in devices_urls.split(','):
            logger.debug('Notifying an update to %s', url)
            inactive_url = '{}/suit/slot/inactive'.format(url)
            _, payload = await coap_request(inactive_url,
                                            method=GET)
            if int(payload) == 1:
                manifest_url = slot1_manifest_url
            else:
                manifest_url = slot0_manifest_url
            payload = '{}://{}:{}/{}'.format(COAP_METHOD, options.coap_host,
                                             options.coap_port, manifest_url)
            logger.debug('Manifest url is %s', payload)
            notify_url = '{}/suit/trigger'.format(url)
            logger.debug('Send update notification at %s', url)
            await coap_request(notify_url, payload=payload.encode())


class OTAServerPublishHandler(tornado.web.RequestHandler):
    """Handler for storing published firmwares."""

    def _store(self, store_url, data):
        _store_path = os.path.join(self.application.upload_path, store_url)
        if not os.path.exists(_store_path):
            os.makedirs(_store_path)

        # Store each data in separate files
        for name, content in data.items():
            _path = os.path.join(_store_path, name)
            logger.debug('Storing file %s', _path)
            with open(_path, 'wb') as f:
                f.write(content)
            # Hack to determine if the file is a manifest and copy as latest
            _path_split = _path.split('.')
            if 'suit' == _path_split[-3]:
                _path_split[-2] = 'latest'
            _path = '.'.join(_path_split)
            with open(_path, 'wb') as f:
                f.write(content)

    async def post(self):
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
            filename = os.path.basename(file)
            update_data[filename] = files[file][0]['body']

        # Get publish identifier
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        # Cleanup the path
        store_path = _path_from_publish_id(publish_id)
        logger.debug('Storing %s update', publish_id)

        # Store the data and create the corresponding CoAP resources
        self._store(store_path, update_data)
        if options.with_coap_server:
            self.application.coap_server.add_resources(store_path)


class OTAServerApplication(web.Application):
    """Tornado based web application providing the OTA server."""

    def __init__(self):
        if options.debug:
            logger.setLevel(logging.DEBUG)

        handlers = [
            (r"/", OTAServerMainHandler),
            (r"/publish", OTAServerPublishHandler),
            (r"/notify", OTAServerNotifyHandler),
            (r"/coap/url/.*", OTAServerCoapUrlHandler),
        ]

        self.upload_path = options.upload_path
        self.firmwares = os.listdir(self.upload_path)

        settings = dict(debug=True,
                        static_path=options.static_path,
                        template_path=options.static_path,)

        if options.with_coap_server:
            self.coap_server = CoapServer(self.upload_path,
                                          port=options.coap_port)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.http_port))
