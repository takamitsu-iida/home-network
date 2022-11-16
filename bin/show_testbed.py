#!/usr/bin/env python

#
# テストベッドのデバイスを表示
#

import logging
import os

from pprint import pprint

#
# import pyATS module
#
from genie.testbed import load
from pyats.utils.secret_strings import to_plaintext


app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')
pyats_dir = os.path.join(lib_dir, 'pyats_util')

logger = logging.getLogger(__name__)


def first_value(d:dict):
    for v in d.values():
        return v


def extract(dev):

    d = {}

    conn_defaults = dev.connections.get('defaults', None)

    if conn_defaults is None:
        # 先頭を選ぶ
        conn = first_value(dev.connections)
    else:
        via = conn_defaults.get('via', None)
        if via is None:
            # 先頭を選ぶ
            conn = first_value(dev.connections)
        else:
            conn = dev.connections.get(via, {})

    ip = conn.get('ip', '')
    d['ip'] = str(ip)

    cred =  conn.get('credentials', {}).get('default', {})

    username = cred.get('username', '')
    password = to_plaintext(cred.get('password', ''))

    d['username'] = username
    d['password'] = password

    return d


if __name__ == '__main__':

    import argparse
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default=os.path.join(pyats_dir, 'home.yaml'))
    args, _ = parser.parse_known_args()

    logger.info(f'testbed file: args.testbed')


    def main():

        testbed = load(args.testbed)

        for name, dev in testbed.devices.items():
            d = extract(dev)
            d['name'] = name
            pprint(d)

        return 0

    sys.exit(main())
