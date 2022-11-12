#!/usr/bin/env python

import logging
import os

from datetime import datetime

#
# tinydb
#
from tinydb import Query, TinyDB

DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, 'db.json')

TABLE_PYATS = 'PYATS'
TABLE_MAC_VENDORS = 'MAC_VENDORS'

DEFAULT_MAX_HISTORY = 10

logger = logging.getLogger(__name__)

def insert_device_data(device_name:str, doc_type:str, doc_data:dict, timestamp:float, max_history=DEFAULT_MAX_HISTORY):
    """
    データを'PYATS'テーブルに保存する。

    格納するドキュメントの形式はこの通り
    {
       'device_name': xxx,
       'doc_type': xxx,
       'doc_data': {},
       'timestamp': xxx
    }

    Args:
        device_name (str): 学習した装置の名前
        doc_type (str): 格納するデータのタイプ 例： mac_address_table
        doc_data (object): 格納するデータ
        timestamp (float): 実行した時点のタイムスタンプ
        max_history (int, optional): 何個まで保存するか Defaults to DEFAULT_MAX_HISTORY.
    """

    # 格納するドキュメント
    doc = {}

    # デバイス名を付与
    doc['device_name'] = device_name

    # ドキュメントタイプを付与
    doc['doc_type'] = doc_type

    # ドキュメントデータを付与
    doc['doc_data'] = doc_data

    # タイムスタンプを付与
    doc['timestamp'] = timestamp

    # PYATSテーブルに格納
    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_PYATS)
        table.insert(doc)

    # max_historyを超えた古いものを削除
    delete_old_device_data(device_name, doc_type, max_history)


def delete_old_device_data(device_name:str, doc_type:str, max_history:int):
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_PYATS)

        # device_nameが一致するドキュメントからtimestampキーの一覧を取り出す
        docs = table.search((q.device_name == device_name) & (q.doc_type == doc_type))
        timestamps = [doc['timestamp'] for doc in docs]

        # 新しい順（降順）にソート
        timestamps.sort(reverse=True)

        # max_historyを超えたものを削除
        if len(timestamps) > max_history:
            should_be_deleted = timestamps[max_history:]
            for ts in should_be_deleted:
                table.remove( (q.device_name == device_name) & (q.timestamp == ts) )


def delete_device_documents(device_name:str, doc_type:str):
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_PYATS)
        table.remove( (q.device_name == device_name) & (q.doc_type == doc_type))


def get_device_documents(device_name:str, doc_type:str):
    """
    デバイス名とドキュメントタイプで検索し、タイムスタンプでソートして返却

    Args:
        device_name (str): 検索対象のキーdevice_nameの値
        doc_type (str): ドキュメントタイプ

    Returns:
        list: 見つかったドキュメントのリスト
    """
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_PYATS)
        docs = table.search((q.device_name == device_name) & (q.doc_type == doc_type))

    if docs:
        return sorted(docs, key=lambda d: d['timestamp'], reverse=True)

    return []


def get_device_document_latest(device_name:str, doc_type:str):
    docs = get_device_documents(device_name=device_name, doc_type=doc_type)
    if len(docs) > 0:
        return docs[0]
    return None


def get_device_document_dates(device_name:str, doc_type:str):

    # 名前でドキュメントを取り出す
    docs = get_device_documents(device_name, doc_type)

    # timestampキーの一覧を取り出す
    timestamps = [doc['timestamp'] for doc in docs]

    # 降順にソートする
    timestamps.sort(reverse=True)

    # datetimeオブジェクトに変換
    datetimes = [datetime.fromtimestamp(ts) for ts in timestamps]

    # 分かりやすく日付の文字列に変換
    dates = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in datetimes]

    return dates


def insert_device_mac_address_table(device_name:str, mac_address_table:dict, timestamp:float, max_history=DEFAULT_MAX_HISTORY):
    """
    parse('show mac address-table')をデータベースに保存する。

    Args:
        device_name (str): 学習した装置の名前
        mac_address_table (dict): parse()したMACアドレステーブル
        timestamp (float): 実行した時点のタイムスタンプ
        max_history (int, optional): 何個まで保存するか Defaults to DEFAULT_MAX_HISTORY.
    """
    insert_device_data(device_name, 'mac_address_table', mac_address_table, timestamp, max_history)


def get_device_mac_address_table(device_name:str):
    """
    名前で検索し、タイムスタンプでソートして返却

    Args:
        device_name (str): 検索対象のキーdevice_nameの値

    Returns:
        list: 見つかったドキュメントのリスト
    """
    return get_device_documents(device_name, 'mac_address_table')


def insert_device_intf_info(device_name:str, intf_info:dict, timestamp:float, max_history=2):
    """
    学習したインタフェース情報をデータベースに保存する。

    Args:
        device_name (str): 学習した装置の名前
        intf_info (dict): 学習したインタフェース情報
        timestamp (float): 実行した時点のタイムスタンプ
        max_history (int, optional): 何個まで保存するか Defaults to 2.
    """
    insert_device_data(device_name, 'intf_info', intf_info, timestamp, max_history)


def get_device_intf_info(device_name:str):
    """
    名前で検索し、タイムスタンプでソートして返却

    Args:
        device_name (str): 検索対象のキーdevice_nameの値

    Returns:
        list: 見つかったドキュメントのリスト
    """
    return get_device_documents(device_name, 'intf_info')


def insert_mac_vendors(mac_vendors_list:list, timestamp:float, table_name=TABLE_MAC_VENDORS):
    """
    データを'TABLE_MAC_VENDORS'テーブルに保存する。

    格納するドキュメントの形式はこの通り
    { 'timestamp': xxx }
    { 'macPrefix': '00:00:0C', 'vendorName': 'Cisco Systems, Inc', ... }
    { 'macPrefix': '98:86:8B', 'vendorName': 'Juniper Networks', ...}

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


def delete_mac_vendors_table(table_name=TABLE_MAC_VENDORS):
    with TinyDB(DB_PATH) as db:
        db.drop_table(table_name)


def get_mac_vendors_timestamp(table_name=TABLE_MAC_VENDORS):
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)

        searched = table.get(q.timestamp.exists())
        if searched is None:
            return None
        return searched['timestamp']


def get_mac_vendors_all(table_name=TABLE_MAC_VENDORS) -> list:
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)

        # {'timestamp': ...}を除くすべて、を返却
        # return table.search(~ (q.timestamp.exists()))

        # {'macPrefix': ...}を含むすべて、を返却
        return table.search(q.macPrefix.exists())


# radix treeを使えば簡単に検索できるけど、ここでは力技で検索
# このやり方は効率が悪くて遅いので廃止
def _search_mac_vendors(mac_address:str, table_name=TABLE_MAC_VENDORS) -> list:

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


def search_mac_vendors(mac_address:str, table_name=TABLE_MAC_VENDORS) -> list:

    # 前提はAA:AA:AA:AA:AA:AAの形式

    # 大文字に変換
    mac_address = mac_address.upper()

    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        # str.find()で一致するかテスト、一致しなければ-1、一致すればその場所が帰ってくる
        return table.search(q.macPrefix.test(lambda s: mac_address.find(s) == 0))


def _dump_mac_vendors(table_name=TABLE_MAC_VENDORS):
    mac_vendors = get_mac_vendors_all()
    # MA-L = 8, MA-M = 10, MA-S = 13
    for prefix_len in [8, 10, 13]:
        for d in mac_vendors:
            prefix = d.get('macPrefix')
            if len(prefix) == prefix_len:
                print(d)


if __name__ == '__main__':

    import sys

    logging.basicConfig(level=logging.INFO)

    def test_mac_vendors_table():

        table_name = 'TEST_MAC_VENDORS'

        mac_vendors_list = [
            # MA-L
            {'macPrefix': '98:86:8B', 'vendorName': 'Juniper Networks'},
            {'macPrefix': '90:31:4B', 'vendorName': 'AltoBeam Inc.'},
            {'macPrefix': 'D8:63:8C', 'vendorName': 'Shenzhen Dttek Technology Co., Ltd.'},

            # MA-M
            {'macPrefix': '8C:5D:B2:9', 'vendorName': 'ISSENDORFF KG'},
            {'macPrefix': '8C:5D:B2:8', 'vendorName': 'Guangzhou Phimax Electronic Technology Co.,Ltd'},
            {'macPrefix': '8C:5D:B2:3', 'vendorName': 'Yuzhou Zhongnan lnformation Technology Co.,Ltd'},

            # MA-S
            {'macPrefix': '8C:1F:64:A5:E', 'vendorName': 'XTIA Ltd'},
            {'macPrefix': '8C:1F:64:FD:C', 'vendorName': 'Nuphoton Technologies'},
            {'macPrefix': '8C:1F:64:43:D', 'vendorName': 'Solid State Supplies Ltd'}
        ]

        # 既存のテスト用テーブルを破棄
        delete_mac_vendors_table(table_name=table_name)

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

        assert [] == search_mac_vendors('AB:CD:EF', table_name=table_name), f"expect: [], got: {search_mac_vendors('AB:CD:EF', table_name=table_name)}"
        logger.info('test non-existent prefix search pass')

        # 既存のテスト用テーブルを破棄
        delete_mac_vendors_table(table_name=table_name)
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
                print(f'{mac} : {searched[0]}')
            else:
                print(f'{mac} not found.')


    def test_insert_device_data():
        device_name = os.uname()[1]

        doc_data = {
            'test_key': 'test_data'
        }

        timestamp = datetime.now().timestamp()

        insert_device_data(device_name=device_name, doc_type='test', doc_data=doc_data, timestamp=timestamp, max_history=DEFAULT_MAX_HISTORY)

        docs = get_device_documents(device_name=device_name, doc_type='test')

        print(f'numbered of stored data is {len(docs)}')
        for doc in docs:
            print(doc)


    def main():
        # test_mac_vendors_table()
        test_mac_vendors_search()
        #_dump_mac_vendors()
        # test_insert_device_data()
        return 0

    sys.exit(main())
