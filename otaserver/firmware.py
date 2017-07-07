"""Common helpers"""

import os
import time
import re
import logging
from stat import ST_SIZE, ST_MTIME

# Firmware filename is in the form: firmware_name-<slot>-<appid>-<version>.bin

FILE_EXT = '.bin'
VERSION_RE = re.compile("0x[0-9]+")
APPID_RE = re.compile("0x[a-zA-Z0-9]+")
SLOT_RE = re.compile("slot[1-2]")


def get_info_from_filename(filename):
    """Get firmware information from filename."""
    return os.path.splitext(filename)[0].split('-')[-3:]

class Firmware(object):
    """Handle meta information of a firmware binary file."""

    def __init__(self, fname):
        self.fname = fname

    def __eq__(self, other):
        return self.fname == other.fname

    def __neq__(self, other):
        return self.fname != other.fname

    def __hash__(self):
        """Hash of firmware filename."""
        return hash(self.fname)

    def check_filename(self):
        """Check if firmware filename is correct."""
        fname, ext = os.path.splitext(os.path.basename(self.fname))
        if ext != FILE_EXT:
            logging.warning("Invalid file extention ('{}'), '.bin' "
                            "is expected.".format(ext))
            return False

        if not VERSION_RE.match(fname.split("-")[-1]):
            logging.warning("Invalid version '{}'"
                            .format(fname.split("-")[-1]))
            return False

        if not APPID_RE.match(fname.split("-")[-2]):
            logging.warning("Invalid application identifier '{}'"
                            .format(fname.split("-")[-2]))
            return False

        if not SLOT_RE.match(fname.split("-")[-3]):
            logging.warning("Invalid slot '{}'"
                            .format(fname.split("-")[-3]))
            return False

        return True

    @property
    def filename(self):
        """Get firmware filename."""
        return self.fname

    @property
    def version(self):
        """Get firmware version."""
        return get_info_from_filename(self.fname)[2]

    @property
    def application_id(self):
        """Get firmware application identifier."""
        return get_info_from_filename(self.fname)[1]

    @property
    def slot(self):
        """Get firmware slot."""
        return get_info_from_filename(self.fname)[0]

    @property
    def size(self):
        """Return the size in Bytes of the firmware."""
        return os.stat(self.fname)[ST_SIZE]

    @property
    def upload_time(self):
        """Return the creation time of the firmware file (upload time)."""
        return time.asctime(time.localtime(os.stat(self.fname)[ST_MTIME]))
