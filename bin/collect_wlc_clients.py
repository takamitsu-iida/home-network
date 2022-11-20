#!/usr/bin/env python

#
# Mobility ExpressのAironet WLCからクライアント情報を取得します
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
from db_util import insert_wlc_clients

# lib/pyats_util/pyats_util.py
from pyats_util import get_inventory

# lib/netmiko_util/netmiko_util.py
from netmiko_util import CiscoWlcHandler

# lib/daemon_util/daemon_util.py
from daemon_util import SingleDaemon

logger = logging.getLogger(__name__)


def update_db_func(ip: str, username: str, password: str) -> callable:
    wlc = CiscoWlcHandler(ip, username, password)

    def _update_db():
        timestamp = datetime.now().timestamp()
        with wlc:
            wlc_clients = wlc.get_wlc_clients()
        insert_wlc_clients(wlc_clients_list=wlc_clients, timestamp=timestamp)

    return _update_db


def update_db(ip: str, username: str, password: str) -> list:

    # 現在時刻
    timestamp = datetime.now().timestamp()

    # WLCに接続している無線端末の情報を採取
    with CiscoWlcHandler(ip, username, password) as wlc:
        wlc_clients = wlc.get_wlc_clients()

    # データベースに格納
    insert_wlc_clients(wlc_clients_list=wlc_clients, timestamp=timestamp)

    return wlc_clients


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

    # 毎時30分に実行
    schedule.every().hour.at(':30').do(func)

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

    parser = argparse.ArgumentParser(description='show wlc clients')
    parser.add_argument('-d', '--daemon', action='store_true', default=False, help='run as daemon')
    parser.add_argument('-k', '--kill', action='store_true', default=False, help='kill running daemon')
    parser.add_argument('-c', '--clear', action='store_true', default=False, help='clear junk pid file')
    parser.add_argument('-g', '--get', action='store_true', default=False, help='get mac address table info')
    args = parser.parse_args()

    def main():
        # pyATSのテストベッドからWLCに関する情報を取得
        inventory = get_inventory('home.yaml', 'wlc')
        ip = inventory.get('ip')
        username = inventory.get('username')
        password = inventory.get('password')

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
            d.start_daemon(run_schedule, update_db_func(ip, username, password))
            return 0

        if args.get:
            with CiscoWlcHandler(ip, username, password) as wlc:
                wlc_clients = wlc.get_wlc_clients()
            pprint(wlc_clients)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
