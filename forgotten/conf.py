# -*- coding: utf-8 -*-
#
# forgotten
# https://github.com/rmed/forgotten
#
# The MIT License (MIT)
#
# Copyright (c) 2017 Rafael Medina García <rafamedgar@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Configuration parsing."""

import logging
import os
import sys
from configparser import ConfigParser

import records


# Parse configuration file
SETTINGS = {}

def parse_conf():
    """Parse the configuration file and set relevant variables.

    The absolute path to the file must be specified in the 'FORGOTTEN_CONF'
    environment variable.

    An example config file is as follows:

        [tg]
        token = 1234567
        owner = 123

        [core]
        db_path = /path/to/db.sqlite
        wait_time = 15
    """
    conf_path = os.path.abspath(os.getenv('FORGOTTEN_CONF', ''))

    if not conf_path or not os.path.isfile(conf_path):
        sys.exit('Could not find configuration file')

    parser = ConfigParser()
    parser.read(conf_path)

    # settings = {}

    # Telegram bot settings
    SETTINGS['token'] = parser['tg']['token']
    SETTINGS['owner'] = int(parser['tg'].get('owner', '-1'))

    # Database
    SETTINGS['db_path'] = parser['core']['db_path']

    # Worker
    SETTINGS['wait_time'] = int(parser['core'].get('wait_time', '15')) * 60

def get_logger(name):
    """Get a logger with the given name."""
    # Base logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Handler to stdout
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Formatting
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s[%(funcName)s]: %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def init_db(db_path):
    """Initialize the database connection.

    If the database file does not exist, it will be created.

    Args:
        db_path (str): Path to the database

    Returns:
        Database connector (SQLite)
    """
    try:
        db = records.Database('sqlite:///%s?check_same_thread=False' % db_path)

    except Exception as e:
        sys.exit('Could not initialize database: %s' % e)

    return db
