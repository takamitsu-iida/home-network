#!/usr/bin/env python

#
# 未知のMACアドレスが登場したら通知します
#

import logging
import os
import sys
import time

from pprint import pformat

import schedule
import yaml

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/pyats_util/pyats_util.py
from pyats_util import get_inventory

# lib/netmiko_util/netmiko_util.py
from netmiko_util import CiscoWlcHandler

# lib/line_util/line_util.py
from line_util import send_line_notify

# lib/daemon_util/daemon_util.py
from daemon_util import SingleDaemon

# lib/db_util/dictfilter.py
from db_util import find_values

#
# logディレクトリ
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app_name = os.path.splitext(os.path.basename(__file__))[0]
log_dir = os.path.join(app_dir, 'log')
log_file = app_name + '.log'
log_path = os.path.join(log_dir, log_file)
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger(__name__)

#
# 既知デバイスのファイル
#
KNOWN_DEVICES_FILE = 'known_devices.yaml'
KNOWN_DEVICES_PATH = os.path.join(app_dir, KNOWN_DEVICES_FILE)


def load_yaml(file_path: str) -> dict:
    """
    YAMLファイルを読み取って辞書型にして返却する

    Args:
        file_path (str): YAMLファイルのパス

    Returns:
        dict: 読み取ったデータ
    """
    try:
        with open(file_path) as f:
            try:
                d = yaml.safe_load(f)
                return d
            except yaml.YAMLError as e:
                logger.error(e)
    except OSError as e:
        logger.error(e)
    return None


def get_known_mac_addresses(known_device_file: str = KNOWN_DEVICES_PATH) -> list:
    """
    KNOWN_DEVICES_PATHに指定されたパスのYAMLファイルをロードして、'mac'キーの値をリストにして返却する

    Args:
        known_device_file (str, optional): YAMLファイルのパス. Defaults to KNOWN_DEVICES_PATH.

    Returns:
        list: 全ての'mac'キーの値をリストにして返却
    """
    # known_devices.yamlをロードする
    known_devices = load_yaml(known_device_file)
    if known_devices is None:
        logger.error(f'known device not found in : {KNOWN_DEVICES_PATH}')
        return []

    # 辞書型の中にある'mac'キーの値を全て取り出して返却する
    return list(find_values(known_devices, 'mac'))


def detect_unknown_wlc_clients(wlc_clients: list) -> list:

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

    # 既知のMACアドレスを調べる
    known_mac = get_known_mac_addresses()

    unknown_mac = []
    for client in wlc_clients:
        mac = client.get('mac_address', None)
        if mac is None:
            continue
        mac = mac.upper()
        if mac not in known_mac:
            unknown_mac.append(client)
    return unknown_mac


def run_func() -> callable:

    # pyATSのテストベッドからWLCに関する情報を取得
    inventory = get_inventory('home.yaml', 'wlc')
    wlc_ip = inventory.get('ip')
    wlc_username = inventory.get('username')
    wlc_password = inventory.get('password')

    # WLCを操作するハンドラをインスタンス化
    wlc = CiscoWlcHandler(wlc_ip, wlc_username, wlc_password)

    # 一度通知したものはここに格納して、次からは発報しない
    reported_mac = []

    # この関数を返却する
    def _run():
        logger.info('connect to WLC')

        # WLCに接続してクライアント情報を採取
        with wlc:
            wlc_clients = wlc.get_wlc_clients()

        # 採取したクライアントのうち、未知のMACアドレスを取り出す
        unknown_mac = detect_unknown_wlc_clients(wlc_clients=wlc_clients)

        if len(unknown_mac) > 0:
            for d in unknown_mac:
                # {'ap_mac_address': '70:ea:1a:84:16:c0',
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
                mac = d.get('mac_address')
                mac = mac.upper()
                logger.info(f'unknown mac detedted: {mac}')
                if mac not in reported_mac:
                    reported_mac.append(mac)
                    message = f'unknown device found.\n{pformat(d)}'
                    logger.error(message)
                    send_line_notify(message)

    return _run


def run_schedule(func: callable):
    """
    scheduleモジュールを利用して定期実行する

    schedule.every(1).minutes.do(dummy, args, kwargs)  # 毎分実行
    schedule.every(1).hours.do(dummy, args, kwargs)    # 毎時実行
    schedule.every().hour.at(':30').do(dummy)          # 毎時30分時点で実行
    schedule.every().minute.at(':30').do(dummy)        # 毎分30秒時点で実行
    schedule.every().day.at('12:10').do(dummy)         # 毎日12時10分時点で実行

    Args:
        ip (str): 対象装置のIPアドレス
        username (str): 対象装置のログインユーザ名
        password (str): 対象装置のログインパスワード
    """

    # 10分ごとに実行
    schedule.every(10).minutes.do(func)

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

    # ログレベル設定
    logger.setLevel(logging.INFO)

    # フォーマット
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 標準出力へのハンドラ
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(logging.INFO)
    logger.addHandler(stdout_handler)

    # ログファイルのハンドラ
    file_handler = logging.FileHandler(log_path, 'a+')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    parser = argparse.ArgumentParser(description='detect unknown device')
    parser.add_argument('-t', '--test', action='store_true', help='test run')
    parser.add_argument('-d',
                        '--daemon',
                        action='store_true',
                        default=False,
                        help='run as daemon')
    parser.add_argument('-k',
                        '--kill',
                        action='store_true',
                        default=False,
                        help='kill running daemon')
    parser.add_argument('-c',
                        '--clear',
                        action='store_true',
                        default=False,
                        help='clear junk pid file')
    args = parser.parse_args()

    def main():

        # PIDファイルはlogディレクトリに保存
        pid_dir = os.path.join(app_dir, 'log')
        pid_file = os.path.basename(__file__) + '.pid'

        if args.test:
            func = run_func()
            func()
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
            logger.info(f'{__file__} started')
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.start_daemon(run_schedule, run_func())
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
