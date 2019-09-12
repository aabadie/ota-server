"""Broker application module."""

import os
import os.path
import logging
import json
import datetime
import asyncio

from collections import defaultdict

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


def _get_versions_from_path(path):
    files = os.listdir(path)
    versions = defaultdict(dict)
    for file in files:
        version = file.split('.')[-2]
        if version == 'latest':
            continue
        if version == 'riot':
            version = file.split('.')[-3]
        if 'riot.suit' in file:
            versions[version]['manifest'] = file
        if 'slot0' in file:
            versions[version]['slot0'] = file
        if 'slot1' in file:
            versions[version]['slot1'] = file
    return versions


def _get_applications(path):
    applications = []
    for d in os.listdir(path):
        board, name = d.split('_', 1)
        applications.append(
            { 'id': d,
              'name': name,
              'board': board,
              'count':int((len(os.listdir(os.path.join(path, d))) - 1) / 3),
              'versions': _get_versions_from_path(os.path.join(path, d))
            })
    return applications


class OTAServerMainHandler(web.RequestHandler):
    """Web application handler for web page."""

    def get(self):
        logger.debug("Rendering SUIT updates web page")
        applications = _get_applications(options.upload_path)
        self.render("otaserver.html",
                    favicon=os.path.join("assets", "favicon.ico"),
                    title="SUIT Update Server",
                    applications=applications,
                    host=options.http_host,
                    port=options.http_port,
                    demo_host=options.demo_host,
                    demo_port=options.demo_port)


class OTAServerRemoveHandler(tornado.web.RequestHandler):
    """Handler for removing an existing version."""

    async def post(self):
        """Handle request for removing an existing version."""
        request = json.loads(self.request.body.decode())
        logger.debug("Removing version %s in application %s",
                     request['version'], request['publish_id'])
        for publish_id in os.listdir(options.upload_path):
            if publish_id == request['publish_id']:
                for filename in os.listdir(
                        os.path.join(options.upload_path, publish_id)):
                    if str(request['version']) not in filename:
                        continue
                    logger.debug("Removing file %s", filename)
                    file = os.path.join(
                        options.upload_path, publish_id, filename)
                    if os.path.exists(file):
                        os.remove(file)


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


class OTAServerNotifyv4Handler(tornado.web.RequestHandler):
    """Handler for notifying an update to a list of devices."""

    async def post(self):
        """Handle notification of an available update."""
        version = self.request.body_arguments['version'][0].decode()
        publish_id = self.request.body_arguments['publish_id'][0].decode()
        publish_path = _path_from_publish_id(publish_id)

        _store_path = os.path.join(self.application.upload_path, publish_id)
        base_filename = os.listdir(_store_path)[0].split('-')[0]

        manifest_url = os.path.join(
            publish_path,
            '{}-riot.suitv4_signed.{}.bin'.format(base_filename, version))

        devices_urls = self.request.body_arguments['urls'][0].decode()
        logger.debug('Notifying devices %s of an update of %s',
                     devices_urls, publish_id)

        for url in devices_urls.split(','):
            logger.debug('Notifying an update to %s', url)
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
            if 'suit' == _path_split[-3] or 'suitv4_signed' == _path_split[-3]:
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
            (r"/remove", OTAServerRemoveHandler),
            (r"/notify", OTAServerNotifyHandler),
            (r"/notifyv4", OTAServerNotifyv4Handler),
            (r"/coap/url/.*", OTAServerCoapUrlHandler),
        ]

        settings = dict(debug=True,
                        static_path=options.static_path,
                        template_path=options.static_path,)

        self.upload_path = options.upload_path
        if options.with_coap_server:
            self.coap_server = CoapServer(self.upload_path,
                                          port=options.coap_port)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.http_port))
