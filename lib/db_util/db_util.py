#!/usr/bin/env python

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


def insert_mac_vendors(mac_vendors_list:list, timestamp:float):
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
        db.drop_table(TABLE_MAC_VENDORS)

        # テーブルを取得
        table = db.table(TABLE_MAC_VENDORS)

        # タイムスタンプの情報を格納
        table.insert({'timestamp': timestamp})

        # macベンダーのリストを一括で挿入
        table.insert_multiple(mac_vendors_list)

def delete_mac_vendors():
    with TinyDB(DB_PATH) as db:
        db.drop_table(TABLE_MAC_VENDORS)


def get_mac_vendors_timestamp():
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_MAC_VENDORS)

        searched = table.get(q.timestamp.exists())
        if searched is None:
            return None
        return searched['timestamp']


def get_mac_vendors_all():
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_MAC_VENDORS)

        # {'timestamp': ...}を除くすべて
        # return table.search(~ (q.timestamp.exists()))

        # {'macPrefix': ...}を含むすべて
        return table.search(q.macPrefix.exists())

def search_mac_vendors(mac_address:str):
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_MAC_VENDORS)
        return table.get(q.macPrefix == mac_address)


if __name__ == '__main__':

    import sys

    def test_mac_vendors_table():

        mac_vendors_list = [
            {'macPrefix': '8C:5D:B2:9', 'vendorName': 'ISSENDORFF KG'},
            {'macPrefix': '8C:5D:B2:8', 'vendorName': 'Guangzhou Phimax Electronic Technology Co.,Ltd'},
            {'macPrefix': '8C:5D:B2:3', 'vendorName': 'Yuzhou Zhongnan lnformation Technology Co.,Ltd'},
            {'macPrefix': '8C:1F:64:A5:E', 'vendorName': 'XTIA Ltd'},
            {'macPrefix': '8C:1F:64:FD:C', 'vendorName': 'Nuphoton Technologies'},
            {'macPrefix': '8C:1F:64:43:D', 'vendorName': 'Solid State Supplies Ltd'}
        ]

        timestamp = datetime.now().timestamp()

        delete_mac_vendors()

        insert_mac_vendors(mac_vendors_list, timestamp)

        assert timestamp == get_mac_vendors_timestamp()

        assert mac_vendors_list == get_mac_vendors_all()

        assert mac_vendors_list[0] == search_mac_vendors('8C:5D:B2:9')
        assert mac_vendors_list[1] == search_mac_vendors('8C:5D:B2:8')
        assert mac_vendors_list[2] == search_mac_vendors('8C:5D:B2:3')
        assert mac_vendors_list[3] == search_mac_vendors('8C:1F:64:A5:E')
        assert mac_vendors_list[4] == search_mac_vendors('8C:1F:64:FD:C')
        assert mac_vendors_list[5] == search_mac_vendors('8C:1F:64:43:D')

        assert None == search_mac_vendors('ab:cd:ef')

        delete_mac_vendors()


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
        test_mac_vendors_table()
        test_insert_device_data()
        return 0

    sys.exit(main())
