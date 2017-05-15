"""Broker application module."""

import sys
import os.path
import tornado
import logging

from tornado.options import define, options

from .server import OTAServerApplication
from .coap import COAP_PORT

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)14s - '
                           '%(levelname)5s - %(message)s')
logger = logging.getLogger("otaserver")

__STATIC_PATH__ = os.path.join(os.path.dirname(__file__), "static")
__UPLOAD_PATH__ = os.path.join(__STATIC_PATH__, "uploads")


def parse_command_line():
    """Parse command line arguments for IoT broker application."""
    define("static-path",
           default=__STATIC_PATH__,
           help="Static files path (containing npm package.json file).")
    define("upload-path",
           default=__UPLOAD_PATH__,
           help="Path where uploaded files are stored.")
    define("port", default=8080, help="Web application HTTP port.")
    define("coap_port", default=COAP_PORT, help="CoAP server port.")
    define("debug", default=False, help="Enable debug mode.")
    options.parse_command_line()


def run(arguments=[]):
    """Start a broker instance."""
    if arguments != []:
        sys.argv[1:] = arguments

    parse_command_line()

    if options.debug:
        logger.setLevel(logging.DEBUG)

    if not os.path.exists(options.upload_path):
        if options.upload_path == __UPLOAD_PATH__:
            os.makedirs(__UPLOAD_PATH__)
        else:
            logger.error("Upload path doesn't exists, '{}' was given."
                         .format(options.upload_path))
            return

    try:
        # Application ioloop initialization
        if not tornado.platform.asyncio.AsyncIOMainLoop().initialized():
            tornado.platform.asyncio.AsyncIOMainLoop().install()

        app = OTAServerApplication()
        app.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logger.debug("Stopping application")
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == '__main__':
    run()
