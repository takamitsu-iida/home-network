#!/usr/bin/env python

#
# 未知のMACアドレスが登場したら通知します
#

import logging
import os
import sys
import time

import schedule

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/pyats_util/pyats_util.py
from pyats_util import get_inventory

# lib/soft_bank_router/dhcp_clients.py
from soft_bank_router import get_dhcp_clients

# lib/netmiko_util/netmiko_util.py
from netmiko_util import CiscoWlcHandler

# lib/daemon_util/daemon_util.py
from daemon_util import SingleDaemon

logger = logging.getLogger(__name__)


def load_known_devices():
    pass



def detect_unknown_dhcp_clients(dhcp_clients: list):

    # [{'ip': '192.168.122.102', 'mac': 'BC:83:85:CE:44:74'},
    #  {'ip': '192.168.122.103', 'mac': '5E:54:72:B7:19:9F'},

    pass

def detect_unknown_wlc_clients(wlc_clients: list):

    # [{'ap_mac_address': '70:ea:1a:84:16:c0',
    # 'ap_name': 'living-AP1815M',
    # 'client_state': 'Associated',
    # 'connected_for': '23391',
    # 'device_type': 'NintendoWII',
    # 'gateway_address': '192.168.122.1',
    # 'hostname': 'N/A',
    # 'ip_address': '192.168.122.107',
    # 'mac_address': '04:03:d6:d8:57:5f',
    # 'netmask': '255.255.255.0',
    # 'username': 'N/A',
    # 'wireless_lan_network_name': 'taka 11ac'},



    pass



def run_func() -> callable:

    # pyATSのテストベッドからソフトバンク光ルータに関する情報を取得
    inventory = get_inventory('home.yaml', 'softbank-router')
    router_ip = inventory.get('ip')
    router_username = inventory.get('username')
    router_password = inventory.get('password')

    # pyATSのテストベッドからWLCに関する情報を取得
    inventory = get_inventory('home.yaml', 'wlc')
    wlc_ip = inventory.get('ip')
    wlc_username = inventory.get('username')
    wlc_password = inventory.get('password')
    wlc = CiscoWlcHandler(wlc_ip, wlc_username, wlc_password)

    def _run():
        dhcp_clients = get_dhcp_clients(router_ip, router_username, router_password)
        detect_unknown_dhcp_clients(dhcp_clients=dhcp_clients)

        with wlc:
            wlc_clients = wlc.get_wlc_clients()
        detect_unknown_wlc_clients(wlc_clients=wlc_clients)

    return _run


def run_schedule(func: callable):
    """
    scheduleモジュールを利用して定期実行する

    schedule.every(1).minutes.do(dummy, args, kwargs)  # 毎分実行
    schedule.every(1).hours.do(dummy)                  # 毎時実行
    schedule.every().hour.at(':30').do(dummy)          # 毎時30分時点で実行
    schedule.every().minute.at(':30').do(dummy)        # 毎分30秒時点で実行
    schedule.every().day.at('12:10').do(dummy)         # 毎日12時10分時点で実行

    Args:
        ip (str): 対象装置のIPアドレス
        username (str): 対象装置のログインユーザ名
        password (str): 対象装置のログインパスワード
    """

    # 毎時15分に実行
    schedule.every().hour.at(':15').do(func)

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

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='show dhcp clients')
    parser.add_argument('-t', '--test', action='store_true', help='test run')
    parser.add_argument('-d', '--daemon', action='store_true', default=False, help='run as daemon')
    parser.add_argument('-k', '--kill', action='store_true', default=False, help='kill running daemon')
    parser.add_argument('-c', '--clear', action='store_true', default=False, help='clear junk pid file')
    args = parser.parse_args()

    def main():


        # PIDファイルはlogディレクトリに保存
        pid_dir = os.path.join(app_dir, 'log')
        pid_file = os.path.basename(__file__) + '.pid'

        if args.test:

            return 0

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
            d.start_daemon(run_schedule, update_db_func(ip, username, password))
            return 0


        parser.print_help()
        return 0



    sys.exit(main())
