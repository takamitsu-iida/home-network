#!/usr/bin/env python

#
# 未知のMACアドレスが登場したら通知します
#

import logging
import os
import sys
import time

from pprint import pprint, pformat

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

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
log_dir = os.path.join(app_dir, 'log')
os.makedirs(log_dir, exist_ok=True)

#
# logging設定
#

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

# ログをファイルに保存
app_name = os.path.splitext(os.path.basename(__file__))[0]
log_file = app_name + '.log'
file_handler = logging.FileHandler(os.path.join(log_dir, log_file), 'a+')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)


def load_yaml(file_path):
    try:
        with open(file_path) as f:
            try:
                d = yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.error(e)
                return None
    except OSError as e:
        logger.error(e)
        return None
    return d


def get_known_mac_addresses(known_devices: dict):
    devices = known_devices.get('devices', [])
    mac_addresses = []
    for device in devices:
        if device.get('device_mac', None) is not None:
            mac_addresses.append(device.get('device_mac'))
        ether = device.get('ethernet', {})
        if ether.get('mac', None) is not None:
            mac_addresses.append(ether.get('mac'))
        ac = device.get('802.11ac', {})
        if ac.get('mac', None) is not None:
            mac_addresses.append(ac.get('mac'))
        ng = device.get('802.11ng', {})
        if ng.get('mac', None) is not None:
            mac_addresses.append(ng.get('mac'))
    return mac_addresses


def detect_unknown_wlc_clients(wlc_clients: list, known_mac: list) -> list:

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

    # known_devices.yamlをロードする
    known_device = load_yaml(os.path.join(app_dir, 'known_devices.yaml'))
    if known_device is None:
        raise Exception('known device not found')
    known_mac = get_known_mac_addresses(known_devices=known_device)

    # pyATSのテストベッドからWLCに関する情報を取得
    inventory = get_inventory('home.yaml', 'wlc')
    wlc_ip = inventory.get('ip')
    wlc_username = inventory.get('username')
    wlc_password = inventory.get('password')
    wlc = CiscoWlcHandler(wlc_ip, wlc_username, wlc_password)

    reported_mac = []

    # この関数を返す
    def _run():
        with wlc:
            wlc_clients = wlc.get_wlc_clients()

        unknown_mac = detect_unknown_wlc_clients(wlc_clients=wlc_clients, known_mac=known_mac)
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
    schedule.every(1).hours.do(dummy)                  # 毎時実行
    schedule.every().hour.at(':30').do(dummy)          # 毎時30分時点で実行
    schedule.every().minute.at(':30').do(dummy)        # 毎分30秒時点で実行
    schedule.every().day.at('12:10').do(dummy)         # 毎日12時10分時点で実行

    Args:
        ip (str): 対象装置のIPアドレス
        username (str): 対象装置のログインユーザ名
        password (str): 対象装置のログインパスワード
    """

    # 毎時10分に実行
    schedule.every().hour.at(':10').do(func)

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

    parser = argparse.ArgumentParser(description='detect unknown device')
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
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.start_daemon(run_schedule, run_func())
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
