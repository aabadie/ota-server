"""Broker application module."""

import sys
import os.path
import tornado
import logging

from tornado.options import define, options

from server import OTAServerApplication
from coap import COAP_PORT, COAP_HOST

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)14s - '
                           '%(levelname)5s - %(message)s')
logger = logging.getLogger("otaserver")

STATIC_PATH = os.path.join(os.path.dirname(__file__), "static")
UPLOAD_PATH = os.path.join(os.path.dirname(__file__), "firmwares")

def parse_command_line():
    """Parse command line arguments for IoT broker application."""
    define("static-path",
           default=STATIC_PATH,
           help="Static files path (containing npm package.json file).")
    define("upload-path",
           default=UPLOAD_PATH,
           help="Path where uploaded files are stored.")
    define("http_host", default="localhost", help="Web application HTTP host.")
    define("http_port", default=8080, help="Web application HTTP port.")
    define("with_coap_server", default=True, help="Use own CoAP server.")
    define("coap_host", default=COAP_HOST, help="CoAP server host.")
    define("coap_port", default=COAP_PORT, help="CoAP server port.")
    define("root_url", default="", help="Root Url to service Application.")
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
        if options.upload_path == UPLOAD_PATH:
            os.makedirs(UPLOAD_PATH)
        else:
            logger.error("Upload path doesn't exists, '{}' was given."
                         .format(options.upload_path))
            return

    try:
        app = OTAServerApplication()
        app.listen(options.http_port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logger.debug("Stopping application")
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == '__main__':
    run()
