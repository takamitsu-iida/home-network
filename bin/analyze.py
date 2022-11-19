#!/usr/bin/env python

#
# TinyDBに保存されている情報を分析します
# ./analyze -d
# ./analyze -w
# ./analyze -c
# の順に情報が増えます。

import logging
import os
import sys

from datetime import datetime
from pprint import pprint

from tabulate import tabulate

# pyATS
from genie.utils import Dq

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/db_util/db_util.py
from db_util import get_dhcp_clients_documents
from db_util import search_mac_vendors
from db_util import get_wlc_clients_documents
from db_util import get_mac_address_table


logger = logging.getLogger(__name__)


def analyze_dhcp() -> dict:
    known_mac = {}

    # 全件回す
    docs = get_dhcp_clients_documents()
    for doc in docs:
        dhcp_list = doc['doc_data']
        for d in dhcp_list:
            # d はこんな感じ {'ip': a.b.c.d, 'mac': AA:BB:CC:DD:EE:FF}
            mac_address = d['mac'].upper()
            ip_address = d['ip']
            if known_mac.get(mac_address, None) is None:
                known_mac[mac_address] = {}
                known_mac[mac_address]['ip_address'] = ip_address
                # このMACアドレスが何かを調べる
                searched = search_mac_vendors(mac_address=mac_address)
                # 検索結果はこんな感じ
                # [{'blockType': 'MA-L', 'lastUpdate': '2020/08/13', 'macPrefix': '90:9A:4A', 'private': False, 'vendorName': 'TP-LINK TECHNOLOGIES CO.,LTD.'}]

                if searched:
                    known_mac[mac_address]['vendor'] = searched[0]['vendorName']
                else:
                    known_mac[mac_address]['vendor'] = ''

    return known_mac

def tabulate_analyze_dhcp_result(known_mac: dict):
    tabulate_list = []
    for mac, props in known_mac.items():
        ip_address = props.get('ip_address', '')
        vendor = props.get('vendor', '')
        tabulate_list.append([mac, ip_address, vendor])

    # 2番目の要素 vendor でソートする
    tabulate_list = sorted(tabulate_list, key=lambda x: x[2], reverse=True)

    return tabulate(tabulate_list, headers=['mac', 'ip', 'vendor'], tablefmt='github')



def analyze_wlc(known_mac: dict):

    docs = get_wlc_clients_documents()
    for doc in docs:
        # {
        #     'timestamp': float型 タイムスタンプ,
        #     'doc_data': [ {'mac_address': a.b.c.d, 'ap_name': ...}, {}, {}]
        # }

        # timestamp = doc['timestamp']
        doc_data = doc['doc_data']
        for d in doc_data:
            mac_address = d.get('mac_address', '').upper()
            device_type = d.get('device_type', '')
            hostname = d.get('hostname', '')
            ip_address = d.get('ip_address', '')
            ap_name = d.get('ap_name', '')
            ssid = d.get('wireless_lan_network_name', '')

            if known_mac.get(mac_address, None) is None:
                known_mac[mac_address] = {}
                known_mac[mac_address]['ip_address'] = ip_address

            if known_mac[mac_address].get('device_type', None) is None:
                known_mac[mac_address]['device_type'] = device_type

            if known_mac[mac_address].get('hostname', None) is None:
                known_mac[mac_address]['hostname'] = hostname

            if known_mac[mac_address].get('ap_name', None) is None:
                known_mac[mac_address]['ap_name'] = ap_name

            if known_mac[mac_address].get('ssid', None) is None:
                known_mac[mac_address]['ssid'] = ssid

    return known_mac


def tabulate_analyze_wlc_result(known_mac: dict):
    tabulate_list = []
    for mac, props in known_mac.items():
        ip_address = props.get('ip_address', '')
        vendor = props.get('vendor', '')
        device_type = props.get('device_type', '')
        hostname = props.get('hostname', '')
        ap_name = props.get('ap_name', '')
        ssid = props.get('ssid', '')

        tabulate_list.append([mac, ip_address, vendor, device_type, hostname, ap_name, ssid])

    # 2番目の要素 vendor でソートする
    tabulate_list = sorted(tabulate_list, key=lambda x: x[2], reverse=True)

    return tabulate(tabulate_list, headers=['mac', 'ip', 'vendor', 'type', 'hostname', 'ap', 'ssid'], tablefmt='github')


def analyze_catalyst(known_mac: dict):

    docs = get_mac_address_table()

    for doc in docs:

        # {
        #   'device_name': xxx,
        #   'doc_type': xxx,
        #   'doc_data': {},
        #   'timestamp': xxx
        # }

        # timestamp = doc['timestamp']
        device_name = doc['device_name']
        doc_data = doc['doc_data']

        # pprint(doc_data)
        # {'mac_table': {'vlans': {'1': {'mac_addresses': {'0000.5e00.0101': {'interfaces': {'FastEthernet0/7': {'entry_type': 'dynamic',
        #                                                                                                     'interface': 'FastEthernet0/7'}},
        #                                                                     'mac_address': '0000.5e00.0101'},
        #                                                 '002c.c88b.60b8': {'interfaces': {'GigabitEthernet0/2': {'entry_type': 'dynamic',
        #                                                                                                         'interface': 'GigabitEthernet0/2'}},
        # mac_addresses = Dq(doc_data).raw('[mac_table][vlans][1][mac_addresses]')
        mac_addresses = doc_data['mac_table']['vlans']['1']['mac_addresses']
        for mac_addr, d in mac_addresses.items():
            # macアドレスの形式をxx:xx:xx形式にする
            mac_address = mac_addr.replace('.', '')
            mac_address = ':'.join(mac_address[i:i+2] for i in range(0,12,2))
            mac_address = mac_address.upper()
            intf = Dq(d).get_values('interface', 0)

            # c2960cx-8pcのGig0/1はアップリンクなので無視
            if device_name == 'c2960cx-8pc' and intf == 'GigabitEthernet0/1':
                continue

            # c3560c-12pc-sのGig0/2はダウンリンクなので無視
            if device_name == 'c3560c-12pc-s' and intf == 'GigabitEthernet0/2':
                continue

            # print(f'{mac} {intf}')
            if known_mac.get(mac_address, None) is None:
                known_mac[mac_address] = {}
                # このMACアドレスのベンダーコードを調べる
                searched = search_mac_vendors(mac_address=mac_address)
                if searched:
                    known_mac[mac_address]['vendor'] = searched[0]['vendorName']
                else:
                    known_mac[mac_address]['vendor'] = ''

                # IPアドレスはCatalystのMAC学習テーブルからは分からない
                known_mac[mac_address]['ip_address'] = ''
            known_mac[mac_address]['device'] = device_name
            known_mac[mac_address]['intf'] = intf

    return known_mac


def tabulate_analyze_catalyst_result(known_mac: dict):
    tabulate_list = []
    for mac, props in known_mac.items():
        ip_address = props.get('ip_address', '')
        vendor = props.get('vendor', '')
        device_type = props.get('device_type', '')
        hostname = props.get('hostname', '')
        ap_name = props.get('ap_name', '')
        ssid = props.get('ssid', '')
        device = props.get('device', '')
        intf = props.get('intf', '')

        tabulate_list.append([mac, ip_address, vendor, device_type, hostname, ap_name, ssid, device, intf])

    # 2番目の要素 vendor でソートする
    tabulate_list = sorted(tabulate_list, key=lambda x: x[2], reverse=True)

    return tabulate(tabulate_list, headers=['mac', 'ip', 'vendor', 'type', 'hostname', 'ap', 'ssid', device, intf], tablefmt='github')



def search_mac_address_in_pyats(mac_address: str):

    # 形式をCiscoの表記に変える
    mac_address = mac_address.replace(':', '')
    mac_address = '.'.join(mac_address[i:i+4] for i in range(0, 12, 4))
    mac_address = mac_address.lower()

    history = []

    docs = get_mac_address_table()
    for doc in docs:
        ts = doc['timestamp']
        doc_data = doc['doc_data']
        device_name = doc['device_name']
        # pprint(doc_data)
        # {'mac_table': {'vlans': {'1': {'mac_addresses': {'0000.5e00.0101': {'interfaces': {'FastEthernet0/7': {'entry_type': 'dynamic',
        #                                                                                                     'interface': 'FastEthernet0/7'}},
        #                                                                     'mac_address': '0000.5e00.0101'},
        #                                                 '002c.c88b.60b8': {'interfaces': {'GigabitEthernet0/2': {'entry_type': 'dynamic',
        #                                                                                                         'interface': 'GigabitEthernet0/2'}},
        #                                                                     'mac_address': '002c.c88b.60b8'},
        mac_addresses = doc_data['mac_table']['vlans']['1']['mac_addresses']
        if mac_address in mac_addresses.keys():
            intf = Dq(mac_addresses).get_values('interface', 0)

            # c2960cx-8pcのGig0/1はアップリンクなので無視
            if device_name == 'c2960cx-8pc' and intf == 'GigabitEthernet0/1':
                continue

            # c3560c-12pc-sのGig0/2はダウンリンクなので無視
            if device_name == 'c3560c-12pc-s' and intf == 'GigabitEthernet0/2':
                continue

            # タイムスタンプ  → datetime型
            dt = datetime.fromtimestamp(ts)
            date = dt.strftime("%Y-%m-%d %H:%M:%S")
            history.append({'date': date, 'device_name': device_name, 'intf': intf})

    return history



if __name__ == '__main__':

    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dhcp', action='store_true', help='show mac from dhcp')
    parser.add_argument('-w', '--wlc', action='store_true', help='show mac from wlc')
    parser.add_argument('-c', '--catalyst', action='store_true', help='show mac from catalyst')
    parser.add_argument('-s', '--search', dest='search', help='search mac address', type=str)
    args = parser.parse_args()

    def main():

        if args.dhcp:
            known_mac = analyze_dhcp()
            t = tabulate_analyze_dhcp_result(known_mac=known_mac)
            print(t)
            print('')
            num_of_mac = len(known_mac.keys())
            unknown_mac_list = list(filter(lambda value: value['vendor'] == '', known_mac.values()))
            num_of_unknown = len(unknown_mac_list)
            unknown_percent = (num_of_unknown / num_of_mac) * 100
            print(f'- total mac addresses: {num_of_mac}')
            print(f'- unknown vendor: {num_of_unknown} ({unknown_percent:.1f})%')
            return 0

        if args.wlc:
            known_mac = analyze_dhcp()
            known_mac = analyze_wlc(known_mac)
            t = tabulate_analyze_wlc_result(known_mac=known_mac)
            print(t)
            return 0

        if args.catalyst:
            known_mac = analyze_dhcp()
            known_mac = analyze_catalyst(known_mac)
            known_mac = analyze_wlc(known_mac)
            t = tabulate_analyze_catalyst_result(known_mac=known_mac)
            print(t)
            return 0

        if args.search:
            history = search_mac_address_in_pyats(args.search)
            for hist in history:
                pprint(hist)
            return 0


        parser.print_help()
        return 0


    sys.exit(main())