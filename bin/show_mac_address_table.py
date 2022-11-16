#!/usr/bin/env python

#
# show mac address-table
#

import logging
import os
import sys

from datetime import datetime
from pprint import pprint

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

#
# lib/db_util/db_util.py
#
from db_util import insert_device_mac_address_table

#
# lib/pyats_util/pyats_util.py
#
from pyats_util import get_testbed_devices, parse_command

logger = logging.getLogger(__name__)


def parse_mac_address_table(testbed_file:str):

    # これを実行した時点のタイムスタンプ
    timestamp = datetime.now().timestamp()

    devices = get_testbed_devices(testbed_file)
    if not devices:
        return None

    result = {}

    for name, dev in devices.items():
        if dev.type != 'switch':
            continue

        parsed = parse_command(dev, 'show mac address-table')
        if parsed is not None:
            result[name] = parsed

            # データベースにタイムスタンプとともに保存
            insert_device_mac_address_table(name, parsed, timestamp)

    return result


def get_mac_addresses(parse_result:dict):

    # parse_result
    #
    # 'c3560c-12pc-s': {'mac_table': {'vlans': {'1': {'mac_addresses': {'0000.5e00.0101': {'interfaces': {'FastEthernet0/7': {'entry_type': 'dynamic',
    #                                                                                                                          'interface': 'FastEthernet0/7'}},
    #                                                                                       'mac_address': '0000.5e00.0101'},
    #                                                                    '002c.c88b.60b8': {'interfaces': {'GigabitEthernet0/2': {'entry_type': 'dynamic',
    #                                                                                                                             'interface': 'GigabitEthernet0/2'}},
    #                                                                                       'mac_address': '002c.c88b.60b8'},

    result_list = []

    for device, mac_table in parse_result.items():
        # mac_tableは階層が深すぎてfor文だけで回すのは無理があるのでDqを使って絞り込む
        # まずは 'mac_addresses' キーの値だけを全件取り出し、macアドレスの一覧を作成する
        mac_addresses = mac_table.q.contains_key_value('entry_type', 'dynamic').get_values('mac_addresses')

        # 個々のmacアドレスに対して絞り込みをする
        for mac_addr in mac_addresses:
            intf = mac_table.q.contains_key_value('mac_addresses', mac_addr).get_values('interface', 0)
            vlan = mac_table.q.contains_key_value('mac_addresses', mac_addr).get_values('vlans', 0)
            # macアドレスの形式をxx:xx:xx形式にする
            mac = mac_addr.replace('.', '')
            mac = ':'.join(mac[i:i+2] for i in range(0,12,2))
            mac = mac.upper()
            result = {
                'mac_address': mac,
                'device': device,
                'interface': intf,
                'vlan': vlan
            }
            result_list.append(result)

    # result_list
    #
    # [{'device': 'c3560c-12pc-s',
    #   'interface': 'FastEthernet0/7',
    #   'mac_address': '00:00:5E:00:01:01',
    #   'vlan': '1'},
    #  {'device': 'c3560c-12pc-s',
    #   'interface': 'GigabitEthernet0/2',
    #   'mac_address': '00:2C:C8:8B:60:B8',
    #   'vlan': '1'},
    #  {'device': 'c3560c-12pc-s',
    #   'interface': 'GigabitEthernet0/2',
    #   'mac_address': '00:B1:E3:D4:3C:01',
    #   'vlan': '1'},

    return result_list



if __name__ == '__main__':

    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    args, _ = parser.parse_known_args()

    logger.info(f'testbed file: args.testbed')


    def main():
        parsed = parse_mac_address_table(args.testbed)

        if not parsed:
            return 1

        mac_address_list = get_mac_addresses(parsed)

        pprint(mac_address_list)


        return 0

    sys.exit(main())