#!/usr/bin/env python

import logging
import os

# import pyATS module
from pyats.utils.secret_strings import to_plaintext
from genie.testbed import load
from genie.metaparser.util.exceptions import SchemaEmptyParserError
from unicon.core.errors import TimeoutError, StateMachineError, ConnectionError
from unicon.core.errors import SubCommandFailure

logger = logging.getLogger(__name__)


def get_testbed_devices(testbed_filename:str):
    try:
        testbed_path = os.path.join(os.path.dirname(__file__), testbed_filename)
        testbed = load(testbed_path)
    except:
        return None

    return testbed.devices


def get_inventory(testbed_filename:str, device_name:str):

    devices = get_testbed_devices(testbed_filename=testbed_filename)
    if devices is None:
        return None

    dev = devices[device_name]

    conn_defaults = dev.connections.get('defaults', None)
    if conn_defaults is None:
        return None

    via = conn_defaults.get('via', None)
    if via is None:
        return None

    conn = dev.connections.get(via, None)
    if conn is None:
        return None

    d = {}

    ip = conn.get('ip', '')
    d['ip'] = str(ip)

    cred =  conn.get('credentials', {}).get('default', None)
    if cred is None:
        return None

    username = cred.get('username', '')
    password = to_plaintext(cred.get('password', ''))

    d['username'] = username
    d['password'] = password

    return d



def parse_command(dev, command:str):
    # connect
    if not dev.is_connected():
        try:
            dev.connect()
        except (TimeoutError, StateMachineError, ConnectionError) as e:
            logger.error(str(e))
            return None

    # parse
    try:
        parsed = dev.parse(command)
    except (SubCommandFailure, SchemaEmptyParserError) as e:
        logger.error(str(e))
        return None

    # disconnect
    if dev.is_connected():
        dev.disconnect()

    return parsed
