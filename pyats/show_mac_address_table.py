#!/usr/bin/env python

#
# show mac address-table
#

import logging
import sys

from datetime import datetime
from pprint import pprint

# import pyats utility
from pyats_util import get_testbed_devices
from pyats_util import parse_command

# import tinydb utility
from db_util import insert_mac_address_table

logger = logging.getLogger(__name__)


def parse_mac_address_table(testbed_file:str):

    # parse_mac_address_table()を実行した時点の共通のタイムスタンプ
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
            insert_mac_address_table(name, parsed, timestamp)

    return result


def get_mac_addresses(parsed:dict):

    # 'c3560c-12pc-s': {'mac_table': {'vlans': {'1': {'mac_addresses': {'0000.5e00.0101': {'interfaces': {'FastEthernet0/7': {'entry_type': 'dynamic',
    #                                                                                                                          'interface': 'FastEthernet0/7'}},
    #                                                                                       'mac_address': '0000.5e00.0101'},
    #                                                                    '002c.c88b.60b8': {'interfaces': {'GigabitEthernet0/2': {'entry_type': 'dynamic',
    #                                                                                                                             'interface': 'GigabitEthernet0/2'}},
    #                                                                                       'mac_address': '002c.c88b.60b8'},

    result_list = []

    for device, mac_table in parsed.items():
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
            result = {
                'mac_address': mac,
                'device': device,
                'interface': intf,
                'vlan': vlan
            }
            result_list.append(result)

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