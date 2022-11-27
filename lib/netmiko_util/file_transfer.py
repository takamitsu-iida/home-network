#!/usr/bin/env python

#
# ファイル転送の例
#

# netmiko
# https://github.com/ktbyers/netmiko

import logging

# netmiko
from netmiko import ConnectHandler, file_transfer
from netmiko.exceptions import NetmikoAuthenticationException

logger = logging.getLogger(__name__)


if __name__ == '__main__':

    import argparse
    import os
    import sys

    from pprint import pprint

    # テスト用にpyATSのテストベッドからインベントリ情報を取りたいのでlibディレクトリをパスに加える
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    lib_dir = os.path.join(app_dir, 'lib')
    if lib_dir not in sys.path:
        sys.path.append(lib_dir)

    from pyats_util import get_testbed_from_file, get_inventory

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--run', action='store_true')
    args, _ = parser.parse_known_args()

    def main():

        if args.run:
            # pyATSのテストベッドからuutに関する情報を取得
            testbed = get_testbed_from_file(testbed_filename='home.yaml')
            inventory = get_inventory(testbed=testbed, device_name='uut')
            ip = inventory['ip']
            username = inventory['username']
            password = inventory['password']

            device_info = {
                'device_type': 'cisco_ios',
                'host': ip,
                'username': username,
                'password': password,
            }

            try:
                ch = ConnectHandler(**device_info)
            except NetmikoAuthenticationException as e:
                logger.error('authentication failed.')
                raise NetmikoAuthenticationException(f'Failed in ConnectHandler(), Error: {str(e)}') from e

            file_info = {
                'source_file': './abc.txt',
                'dest_file': 'abc.txt',
                'file_system': 'flash:',
                'direction': 'put',
                'overwrite_file': True
            }

            transfer_result = file_transfer(ch, **file_info)
            pprint(transfer_result)

            return 0

        parser.print_help()
        return 0

    sys.exit(main())
