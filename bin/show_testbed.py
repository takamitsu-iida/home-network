#!/usr/bin/env python

#
# テストベッドのデバイスを表示
#

import logging
import os
import sys

from pprint import pprint

#
# import pyATS module
#
from genie.testbed import load
from pyats.utils.secret_strings import to_plaintext

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/pyats_util/pyats_util.py
from pyats_util import get_testbed_from_file, get_inventory

logger = logging.getLogger(__name__)


if __name__ == '__main__':

    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML filename', type=str, default='home.yaml')
    args, _ = parser.parse_known_args()

    logger.info(f'testbed file: args.testbed')

    def main():

        testbed = get_testbed_from_file(args.testbed)

        for device_name, dev in testbed.devices.items():
            inventory = get_inventory(testbed=testbed, device_name=device_name)
            inventory['name'] = device_name
            pprint(inventory)

        return 0

    sys.exit(main())
