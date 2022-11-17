#!/usr/bin/env python

import logging
import os

from datetime import datetime

#
# tinydb
#
from tinydb import Query, TinyDB

# JSONファイル
DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, 'db.json')

# テーブルの種類
TABLE_MAC_VENDORS = 'MAC_VENDORS'

logger = logging.getLogger(__name__)

#
# MACベンダー情報
#

def insert_mac_vendors(mac_vendors_list:list, timestamp:float, table_name:str=TABLE_MAC_VENDORS):
    """
    データを'TABLE_MAC_VENDORS'テーブルに保存する。

    格納するドキュメントの形式はこの通り
    { 'timestamp': xxx }
    { 'macPrefix': '00:00:0C', 'vendorName': 'Cisco Systems, Inc', ... }
    { 'macPrefix': '98:86:8B', 'vendorName': 'Juniper Networks', ...}

    正確にはこんな感じ
    {'blockType': 'MA-L', 'lastUpdate': '2020/08/13', 'macPrefix': '90:9A:4A', 'private': False, 'vendorName': 'TP-LINK TECHNOLOGIES CO.,LTD.'}

    Args:
        mac_vendors_list (list): MACベンダーのdictデータのリスト
        timestamp (float): 実行した時点のタイムスタンプ
    """
    with TinyDB(DB_PATH) as db:
        # すでにテーブルが存在する場合は破棄
        db.drop_table(table_name)

        # テーブルを取得
        table = db.table(table_name)

        # タイムスタンプの情報を格納
        table.insert({'timestamp': timestamp})

        # macベンダーのリストを一括で挿入
        table.insert_multiple(mac_vendors_list)


def get_mac_vendors_timestamp(table_name:str=TABLE_MAC_VENDORS):
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        searched = table.get(q.timestamp.exists())

    if searched is None:
        return None
    return searched['timestamp']


def get_mac_vendors_datetime(table_name:str=TABLE_MAC_VENDORS):
    ts = get_mac_vendors_timestamp(table_name=table_name)
    if ts is None:
        return None
    return datetime.fromtimestamp(ts)


def get_mac_vendors_all(table_name:str=TABLE_MAC_VENDORS) -> list:
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)

        # {'timestamp': ...}を除くすべて、を返却
        # return table.search(~ (q.timestamp.exists()))

        # {'macPrefix': ...}を含むすべて、を返却
        return table.search(q.macPrefix.exists())


# radix treeを使えば簡単に検索できるけど、ここでは力技で検索
# このやり方は効率が悪くて遅いので廃止
def _search_mac_vendors(mac_address:str, table_name:str=TABLE_MAC_VENDORS) -> list:

    # 前提はAA:AA:AA:AA:AA:AAの形式

    # 大文字に変換
    mac_address = mac_address.upper()

    q = Query()

    with TinyDB(DB_PATH) as db:

        table = db.table(table_name)

        # MA-S 36ビットのベンダーコードを検索
        # コロン表記で13文字
        if len(mac_address) >= 13:
            searched = table.search(q.macPrefix == mac_address[:13])
            if len(searched) > 0:
                return searched

        # MA-M 28ビットのベンダーコードを検索
        # コロン表記で10文字
        if len(mac_address) >= 10:
            searched = table.search(q.macPrefix == mac_address[:10])
            if len(searched) > 0:
                return searched

        # MA-L 24ビットのベンダーコードを検索
        # コロン表記で8文字
        if len(mac_address) >= 8:
            searched = table.search(q.macPrefix == mac_address[:8])
            if len(searched) > 0:
                return searched

    return []


def search_mac_vendors(mac_address:str, table_name:str=TABLE_MAC_VENDORS) -> list:
    """
    MACアドレスをキーとしてベンダーを検索する。

    Args:
        mac_address (str): AA:AA:AA:AA:AA:AAの形式の文字列
        table_name (str, optional): _description_. Defaults to TABLE_MAC_VENDORS.

    Returns:
        list: 検索結果。一致したものがなければ空のリスト。
    """

    # 大文字に変換
    mac_address = mac_address.upper()

    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        # str.find()で一致するかテストする
        return table.search(q.macPrefix.test(lambda s: mac_address.find(s) == 0))


def dump_mac_vendors(table_name:str=TABLE_MAC_VENDORS):
    mac_vendors = get_mac_vendors_all()
    # MA-L = 8, MA-M = 10, MA-S = 13

    try:
        for prefix_len in [8, 10, 13]:
            for d in mac_vendors:
                prefix = d.get('macPrefix')
                if len(prefix) == prefix_len:
                    print(d)
    except (BrokenPipeError, IOError):
        # lessにパイプしたときのBrokenPipeError: [Errno 32] Broken pipeを避ける
        sys.stderr.close()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':

    import argparse
    import sys
    from pprint import pprint

    logging.basicConfig(level=logging.INFO)

    def test_mac_vendors_table():

        table_name = 'TEST_MAC_VENDORS'

        mac_vendors_list = [
            # MA-L
            {'macPrefix': '98:86:8B', 'vendorName': 'Juniper Networks'},
            {'macPrefix': '90:31:4B', 'vendorName': 'AltoBeam Inc.'},
            # MA-M
            {'macPrefix': '8C:5D:B2:9', 'vendorName': 'ISSENDORFF KG'},
            {'macPrefix': '8C:5D:B2:8', 'vendorName': 'Guangzhou Phimax Electronic Technology Co.,Ltd'},
            # MA-S
            {'macPrefix': '8C:1F:64:A5:E', 'vendorName': 'XTIA Ltd'},
            {'macPrefix': '8C:1F:64:FD:C', 'vendorName': 'Nuphoton Technologies'},
        ]

        # 既存のテスト用テーブルを破棄
        with TinyDB(DB_PATH) as db:
            db.drop_table(table_name)

        # 現在時刻を取得
        timestamp = datetime.now().timestamp()

        # テストデータを挿入
        insert_mac_vendors(mac_vendors_list, timestamp, table_name=table_name)

        assert timestamp == get_mac_vendors_timestamp(table_name=table_name)
        logger.info('test timestamp: pass')

        assert mac_vendors_list == get_mac_vendors_all(table_name=table_name)
        logger.info('test mac_vendors_all() pass')

        for d in mac_vendors_list:
            prefix = d.get('macPrefix')
            assert [d] == search_mac_vendors(prefix, table_name=table_name)
            if len(prefix) == 13:
                mac_address = prefix + '0:00'
            if len(prefix) == 10:
                mac_address = prefix + '0:00:00'
            if len(prefix) == 8:
                mac_address = prefix + '00:00:00'
            assert [d] == search_mac_vendors(mac_address, table_name=table_name)

        logger.info('test existent prefix search pass')

        assert [] == search_mac_vendors('AB:CD:EF:00:00:00', table_name=table_name)
        logger.info('test non-existent prefix search pass')

        # 既存のテスト用テーブルを破棄
        with TinyDB(DB_PATH) as db:
            db.drop_table(table_name)

        assert None == get_mac_vendors_timestamp(table_name=table_name)


    def test_mac_vendors_search():
        mac_list = [
                    '28:84:fa:ea:5f:0c',
                    '04:03:d6:d8:57:5f',
                    '3c:22:fb:7b:85:0e',
                    '2e:14:db:b8:9b:d8',
                    'fe:dd:b8:3f:de:59',
                    '4c:34:88:93:80:87',
                    '44:65:0d:da:2a:f5',
                    '68:84:7e:87:04:be',
                    'ee:e7:80:e3:c3:b2',
                    '7e:87:0b:67:17:e2',
                    '20:df:b9:b4:bc:79',
                    '38:1a:52:5b:42:15',
                    'a4:5e:60:e4:1a:dd',
                    'c6:78:ad:69:2d:fd',
                    '12:87:66:76:e7:7d',
                    '26:67:ca:be:bc:c9',
                    '90:9a:4a:d6:bb:b9',
                    '08:97:98:04:22:e4',
                    'f6:ff:cc:5f:51:68',
                    '50:eb:f6:95:8b:37']
        for mac in mac_list:
            searched = search_mac_vendors(mac)
            if searched:
                vendor_name = searched[0]['vendorName']
            else:
                vendor_name = 'not found'
            print(f'{mac} = {vendor_name}')

    #
    # main
    #

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true', default=False, help='run test')
    parser.add_argument('-d', '--dump', action='store_true', default=False, help='dump all data')
    parser.add_argument('-s', '--search', dest='search', help='search mac address', type=str)
    args = parser.parse_args()

    def main():
        if args.test:
            test_mac_vendors_table()
            test_mac_vendors_search()
            return 0

        if args.dump:
            dump_mac_vendors()
            return 0

        if args.search:
            searched = search_mac_vendors(mac_address=args.search)
            pprint(searched)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
