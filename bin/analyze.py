#!/usr/bin/env python

#
# Catalystの 'show mac address-table' の出力を収集します
#

import logging
import os
import sys

from datetime import datetime

from tabulate import tabulate

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


logger = logging.getLogger(__name__)


def analyze_dhcp() -> dict:
    known_mac = {}

    # 全件回す
    docs = get_dhcp_clients_documents()
    for doc in docs:
        dhcp_list = doc['doc_data']
        for d in dhcp_list:
            # d はこんな感じ {'ip': a.b.c.d, 'mac': AA:BB:CC:DD:EE:FF}
            mac = d['mac']
            ip = d['ip']
            if known_mac.get(mac, None) is None:
                known_mac[mac] = {}
                known_mac[mac]['ip'] = ip
                # このMACアドレスが何かを調べる
                searched = search_mac_vendors(mac_address=mac)
                # 検索結果はこんな感じ
                # [{'blockType': 'MA-L', 'lastUpdate': '2020/08/13', 'macPrefix': '90:9A:4A', 'private': False, 'vendorName': 'TP-LINK TECHNOLOGIES CO.,LTD.'}]

                if searched:
                    known_mac[mac]['vendor'] = searched[0]['vendorName']
                else:
                    known_mac[mac]['vendor'] = ''

    return known_mac


def analyze_wlc(known_mac: dict):

    docs = get_wlc_clients_documents()
    for doc in docs:






def tabulate_known_mac(known_mac: dict):
    tabulate_list = []
    for mac, props in known_mac.items():
        tabulate_list.append([mac, props['ip'], props['vendor']])

    return tabulate(tabulate_list, headers=['mac', 'ip', 'vendor'], tablefmt='github')



if __name__ == '__main__':

    import argparse

    from pprint import pprint

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dhcp', action='store_true', help='show mac from dhcp table')
    parser.add_argument('-w', '--wlc', action='store_true', help='show mac from wlc table')
    args = parser.parse_args()

    def main():

        if args.dhcp:
            known_mac = analyze_dhcp()
            t = tabulate_known_mac(known_mac=known_mac)
            print(t)
            num_of_mac = len(known_mac.keys())
            unknown_mac_list = list(filter(lambda value: value['vendor'] == '', known_mac.values()))
            num_of_unknown = len(unknown_mac_list)
            print(f'total mac addresses: {num_of_mac}')
            print(f'unknown vendor: {num_of_unknown}')
            return 0

        if args.wlc:
            known_mac = analyze_dhcp()
            known_mac = analyze_wlc(known_mac)



        return 0


    sys.exit(main())