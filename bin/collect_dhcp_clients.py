#!/usr/bin/env python

#
# ソフトバンク光のルータからDHCPの情報を採取します
#

import argparse
import logging
import os
import sys
import time

from datetime import datetime
from pprint import pprint

import schedule

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/db_util/db_util.py
from db_util import insert_dhcp_clients

# lib/pyats_util/pyats_util.py
from pyats_util import get_inventory

# lib/soft_bank_router/dhcp_clients.py
from soft_bank_router import get_dhcp_clients

# lib/daemon_util/daemon_util.py
from daemon_util import SingleDaemon

logger = logging.getLogger(__name__)


def update_db_func(ip: str, username: str, password: str) -> callable:

    def _update_db():
        timestamp = datetime.now().timestamp()
        dhcp_clients = get_dhcp_clients(ip, username, password)
        insert_dhcp_clients(dhcp_clients_list=dhcp_clients, timestamp=timestamp)

    return _update_db


def update_db(ip: str, username: str, password: str) -> list:

    # 現在時刻
    timestamp = datetime.now().timestamp()

    # DHCPクライアントの情報を採取
    dhcp_clients = get_dhcp_clients(ip, username, password)

    # データベースに格納
    insert_dhcp_clients(dhcp_clients_list=dhcp_clients, timestamp=timestamp)

    return dhcp_clients


def run_schedule(func: callable):
    """
    scheduleモジュールを利用して定期実行する

    schedule.every(1).minutes.do(dummy, args, kwargs)  # 毎分実行
    schedule.every(1).hours.do(dummy)                  # 毎時実行
    schedule.every().hour.at(':30').do(dummy)          # 毎時30分時点で実行
    schedule.every().minute.at(':30').do(dummy)        # 毎分30秒時点で実行
    schedule.every().day.at('12:10').do(dummy)         # 毎日12時10分時点で実行

    Args:
        func (callable): 定期実行する関数
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

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='show dhcp clients')
    parser.add_argument('-d', '--daemon', action='store_true', default=False, help='run as daemon')
    parser.add_argument('-k', '--kill', action='store_true', default=False, help='kill running daemon')
    parser.add_argument('-c', '--clear', action='store_true', default=False, help='clear junk pid file')
    parser.add_argument('-g', '--get', action='store_true', default=False, help='get dhcp clients info')
    args = parser.parse_args()

    def main():

        # pyATSのテストベッドからソフトバンク光ルータに関する情報を取得
        inventory = get_inventory('home.yaml', 'softbank-router')
        ip = inventory.get('ip')
        username = inventory.get('username')
        password = inventory.get('password')

        # PIDファイルはlogディレクトリに保存
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
            d.start_daemon(run_schedule, update_db_func(ip, username, password))
            return 0

        if args.get:
            dhcp_clients = get_dhcp_clients(ip, username, password)
            pprint(dhcp_clients)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
