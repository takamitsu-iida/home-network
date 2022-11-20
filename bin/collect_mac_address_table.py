#!/usr/bin/env python

#
# Catalystの 'show mac address-table' の出力を収集します
#

import logging
import os
import sys
import time

from datetime import datetime

import schedule

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/db_util/db_util.py
from db_util import insert_device_mac_address_table

# lib/pyats_util/pyats_util.py
from pyats_util import get_testbed_devices, parse_command

# lib/daemon_util/daemon_util.py
from daemon_util import SingleDaemon


logger = logging.getLogger(__name__)


def update_db_func(testbed_file:str) -> callable:

    def _update_db():
        timestamp = datetime.now().timestamp()
        parsed = parse_mac_address_table(testbed_file)
        for name, parsed_data in parsed.items():
            insert_device_mac_address_table(name, parsed_data, timestamp)

    return _update_db


def update_db(testbed_file:str) -> dict:

    # これを実行した時点のタイムスタンプ
    timestamp = datetime.now().timestamp()

    # 全てのCatalystを対象にpyATSでparse()する
    parsed = parse_mac_address_table(testbed_file)

    for name, parsed_data in parsed.items():
        # 装置ごとにデータベースに保存
        insert_device_mac_address_table(name, parsed_data, timestamp)

    return parsed


def get_mac_addresses(parse_result:dict):

    # parse_result
    #
    # {'c3560c-12pc-s': {'mac_table': {'vlans': {'1': {'mac_addresses': {'0000.5e00.0101': {'interfaces': {'FastEthernet0/7': {'entry_type': 'dynamic',
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


def parse_mac_address_table(testbed_file:str):

    # テストベッドのデバイス一覧を取得
    devices = get_testbed_devices(testbed_file)
    if not devices:
        return None

    # 複数のCatalystの情報を一つにまとめる
    result = {}
    for name, dev in devices.items():
        if dev.type != 'switch':
            continue

        parsed = parse_command(dev, 'show mac address-table')
        if parsed is not None:
            result[name] = parsed

    return result


def run_schedule(func: callable):
    """
    scheduleモジュールを利用して定期実行する

    schedule.every(1).minutes.do(dummy, args, kwargs)  # 毎分実行
    schedule.every(1).hours.do(dummy)                  # 毎時実行
    schedule.every().hour.at(':30').do(dummy)          # 毎時30分時点で実行
    schedule.every().minute.at(':30').do(dummy)        # 毎分30秒時点で実行
    schedule.every().day.at('12:10').do(dummy)         # 毎日12時10分時点で実行

    Args:
        func (callable): 実行する関数
    """

    # 毎時45分に実行
    schedule.every().hour.at(':45').do(func)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except SystemExit:
            break
        except Exception as e:
            logger.info(e)


if __name__ == '__main__':

    import argparse

    from pprint import pprint

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='show mac address table')
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    parser.add_argument('-d', '--daemon', action='store_true', default=False, help='run as daemon')
    parser.add_argument('-k', '--kill', action='store_true', default=False, help='kill running daemon')
    parser.add_argument('-c', '--clear', action='store_true', default=False, help='clear junk pid file')
    parser.add_argument('-g', '--get', action='store_true', default=False, help='get mac address table info')
    args = parser.parse_args()

    def main():

        testbed_file = args.testbed

        # logディレクトリにPIDファイルを作成する
        pid_dir = os.path.join(app_dir, 'log')
        pid_file = os.path.basename(__file__) + '.pid'

        if args.clear:
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.clear()
            return 0

        if args.kill:
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.stop_daemon()
            return 0

        if args.daemon:
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.start_daemon(run_schedule, update_db_func(testbed_file))
            return 0

        if args.get:
            # pyATSでパースして
            parsed = parse_mac_address_table(args.testbed)

            # MACアドレスの情報を抽出して
            mac_address_list = get_mac_addresses(parsed)

            # 表示
            pprint(mac_address_list)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())