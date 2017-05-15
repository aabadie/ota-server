"""Broker application module."""

import re
import os
import os.path
import tornado
import logging
import time
from stat import ST_SIZE, ST_MTIME
from tornado.options import options
from tornado import web
import tornado.platform.asyncio

from .coap import CoapController

logger = logging.getLogger("otaserver")

__VERSION_RE__ = re.compile("[0-9]+\.[0-9]+\.[0-9]+")


def check_fname(fname):
    fname, ext = os.path.splitext(fname)
    if ext != '.elf':
        return False

    return __VERSION_RE__.match(fname.split("-")[-1])


class Firmware(object):

    def __init__(self, fullname, filename):
        self.fullname = fullname
        self.filename = filename

    def __eq__(self, other):
        return self.fullname == other.fullname

    def __neq__(self, other):
        return self.fullname != other.fullname

    def __hash__(self):
        return hash(self.fullname)

    @property
    def size(self):
        return os.stat(self.fullname)[ST_SIZE]

    @property
    def upload_time(self):
        return time.asctime(time.localtime(os.stat(self.fullname)[ST_MTIME]))


class OTAServerMainHandler(web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, path=None):
        os.listdir(self.application.upload_path)

        self.render("otaserver.html",
                    favicon=os.path.join(options.static_path,
                                         "assets", "favicon.ico"),
                    title="OTA Server application",
                    firmwares=self.application.firmwares)


class OTAServerUploadHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def post(self):
        fileinfo = self.request.files['filearg'][0]
        fname = fileinfo['filename']
        fullname = os.path.join(self.application.upload_path, fname)

        # Only manage upload if file is valid
        if check_fname(fname) and not os.path.isfile(fullname):
            with open(fullname, 'wb') as f:
                f.write(fileinfo['body'])
            self.application.firmwares.append(Firmware(fullname, fname))

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
        self.firmwares = [Firmware(os.path.join(self.upload_path, fname),
                                   fname)
                          for fname in os.listdir(self.upload_path)]

        settings = dict(debug=True,
                        static_path=options.static_path,
                        template_path=options.static_path,
                        )
        CoapController(os.path.join(options.static_path, "uploads"),
                       port=options.coap_port)

        super().__init__(handlers, **settings)
        logger.info('Application started, listening on port {}'
                    .format(options.port))
