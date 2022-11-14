#!/usr/bin/env python

#
# 雑多なお試し用
#

import logging
import os

from pprint import pprint

# import pyATS module
from genie.testbed import load


logger = logging.getLogger(__name__)



if __name__ == '__main__':

    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    args, _ = parser.parse_known_args()

    logger.info(f'testbed file: args.testbed')

    def main():

        testbed = load(args.testbed)

        uut = testbed.devices['wlc']

        # connect
        uut.connect()

        parsed = uut.parse('show sysinfo')
        pprint(parsed)

        # disconnect
        if uut.is_connected():
            uut.disconnect()

        return 0

    sys.exit(main())