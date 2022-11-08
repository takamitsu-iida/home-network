#!/usr/bin/env python

import logging

# import pyATS module
from genie.testbed import load
from genie.metaparser.util.exceptions import SchemaEmptyParserError
from unicon.core.errors import TimeoutError, StateMachineError, ConnectionError
from unicon.core.errors import SubCommandFailure

logger = logging.getLogger(__name__)


def get_testbed_devices(testbed_path:str):
    try:
        testbed = load(testbed_path)
    except:
        return None

    return testbed.devices


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
