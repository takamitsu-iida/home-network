#!/usr/bin/env python

#
# show mac address
#

import logging

from datetime import datetime
from pprint import pprint

# import pyATS module
from genie.testbed import load
from unicon.core.errors import TimeoutError, StateMachineError, ConnectionError
from unicon.core.errors import SubCommandFailure
from genie.metaparser.util.exceptions import SchemaEmptyParserError

# import tinydb utility
from db_util import insert_mac_address_table

logger = logging.getLogger(__name__)

if __name__ == '__main__':

    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    args, _ = parser.parse_known_args()

    logger.info(f'testbed file: args.testbed')


    def parse_command(dev, command):
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


    def parse_mac_address_table(testbed_file):

        # parse_mac_address_table()を実行した時点の共通のタイムスタンプ
        timestamp = datetime.now().timestamp()

        testbed = load(testbed_file)

        result = {}

        for name, dev in testbed.devices.items():
            if dev.type != 'switch':
                continue

            parsed = parse_command(dev, 'show mac address-table')
            if parsed is not None:
                result[name] = parsed

                # データベースにタイムスタンプとともに保存
                insert_mac_address_table(name, parsed, timestamp)

        return result



    def main():
        parsed = parse_mac_address_table(args.testbed)
        pprint(parsed)



        return 0

    sys.exit(main())