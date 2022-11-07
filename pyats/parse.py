#!/usr/bin/env python

#
# 雑多なお試し用
#

import logging
import os

from pprint import pprint

# import pyATS module
from genie.testbed import load

# import tinydb module
from tinydb import TinyDB, Query

logger = logging.getLogger(__name__)

#
# tinydb
#
db_dir = os.path.join(os.path.dirname(__file__), 'tinydb')
db_file = os.path.join(db_dir, 'db.json')

# ディレクトリを作成
os.makedirs(db_dir, exist_ok=True)

# dbをロード
db = TinyDB(db_file)


if __name__ == '__main__':

    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='testbed.yaml')
    args, _ = parser.parse_known_args()

    logger.info(f'testbed file: args.testbed')

    def main():

        testbed = load(args.testbed)

        uut = testbed.devices['uut']

        # connect
        uut.connect(via='vty')

        parsed = uut.parse('show version')
        pprint(parsed)

        parsed = uut.parse('show mac address-table')
        pprint(parsed)

        # disconnect
        if uut.is_connected():
            uut.disconnect()

        return 0

    sys.exit(main())