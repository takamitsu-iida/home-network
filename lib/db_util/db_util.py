#!/usr/bin/env python

import os
from datetime import datetime

#
# tinydb
#
from tinydb import Query, TinyDB

DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, 'db.json')

# ディレクトリを作成
os.makedirs(DB_DIR, exist_ok=True)

DEFAULT_MAX_HISTORY = 10

def insert_data(device_name:str, doc_type:str, doc_data:dict, timestamp:float, max_history=DEFAULT_MAX_HISTORY):
    """
    データをデータベースに保存する。

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
        doc_data (dict): 格納するdict型データ
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

    # dbに格納
    with TinyDB(DB_PATH) as db:
        db.insert(doc)

    # この装置に関する古いものを削除
    delete_old(device_name, doc_type, max_history)


def delete_old(device_name:str, doc_type:str, max_history:int):
    q = Query()

    with TinyDB(DB_PATH) as db:
        # device_nameが一致するドキュメントからtimestampキーの一覧を取り出す
        docs = db.search((q.device_name == device_name) & (q.doc_type == doc_type))
        timestamps = [doc['timestamp'] for doc in docs]

        # 新しい順（降順）にソート
        timestamps.sort(reverse=True)

        # max_histを超えたものは削除
        if len(timestamps) > max_history:
            should_be_deleted = timestamps[max_history:]
            for ts in should_be_deleted:
                db.remove( (q.device_name == device_name) & (q.timestamp == ts) )


def get_documents_by_name(device_name:str, doc_type:str):
    """
    名前で検索し、タイムスタンプでソートして返却

    Args:
        device_name (str): 検索対象のキーdevice_nameの値
        doc_type (str): ドキュメントタイプ

    Returns:
        list: 見つかったドキュメントのリスト
    """
    q = Query()

    with TinyDB(DB_PATH) as db:
        datas = db.search((q.device_name == device_name) & (q.doc_type == doc_type))

    if datas:
        return sorted(datas, key=lambda d: d['timestamp'], reverse=True)

    return []


def get_latest_by_name(device_name:str, doc_type:str):
    docs = get_documents_by_name(device_name=device_name, doc_type=doc_type)
    if len(docs) > 0:
        return docs[0]
    return docs


def get_stored_dates(device_name:str, doc_type:str):

    # 名前でドキュメントを取り出す
    docs = get_documents_by_name(device_name, doc_type)

    # timestampキーの一覧を取り出す
    timestamps = [doc['timestamp'] for doc in docs]

    # 降順にソートする
    timestamps.sort(reverse=True)

    # datetimeオブジェクトに変換
    datetimes = [datetime.fromtimestamp(ts) for ts in timestamps]

    # 分かりやすく日付の文字列に変換
    dates = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in datetimes]

    return dates


def insert_mac_address_table(device_name:str, mac_address_table:dict, timestamp:float, max_history=DEFAULT_MAX_HISTORY):
    """
    parse('show mac address-table')をデータベースに保存する。

    Args:
        device_name (str): 学習した装置の名前
        mac_address_table (dict): parse()したMACアドレステーブル
        timestamp (float): 実行した時点のタイムスタンプ
        max_history (int, optional): 何個まで保存するか Defaults to DEFAULT_MAX_HISTORY.
    """
    insert_data(device_name, 'mac_address_table', mac_address_table, timestamp, max_history)


def get_mac_address_table_by_name(device_name:str):
    """
    名前で検索し、タイムスタンプでソートして返却

    Args:
        device_name (str): 検索対象のキーdevice_nameの値

    Returns:
        list: 見つかったドキュメントのリスト
    """
    return get_documents_by_name(device_name, 'mac_address_table')


def insert_intf_info(device_name:str, intf_info:dict, timestamp:float, max_history=2):
    """
    学習したインタフェース情報をデータベースに保存する。

    格納するドキュメントの形式はこの通り
    {
       'timestamp': xxx,
       'device_name': xxx,
       'intf_info': 学習した情報
    }

    Args:
        device_name (str): 学習した装置の名前
        intf_info (dict): 学習したインタフェース情報
        timestamp (float): 実行した時点のタイムスタンプ
        max_history (int, optional): 何個まで保存するか Defaults to 2.
    """
    insert_data(device_name, 'intf_info', intf_info, timestamp, max_history)


def get_intf_info_by_name(device_name:str):
    """
    名前で検索し、タイムスタンプでソートして返却

    Args:
        device_name (str): 検索対象のキーdevice_nameの値

    Returns:
        list: 見つかったドキュメントのリスト
    """
    return get_documents_by_name(device_name, 'intf_info')


if __name__ == '__main__':

    import sys

    def main():

        device_name = os.uname()[1]

        doc_data = {
            'test_key': 'test_data'
        }

        timestamp = datetime.now().timestamp()

        insert_data(device_name=device_name, doc_type='test', doc_data=doc_data, timestamp=timestamp, max_history=DEFAULT_MAX_HISTORY)

        docs = get_documents_by_name(device_name=device_name, doc_type='test')

        print(f'numbered of stored data is {len(docs)}')

        for doc in docs:
            print(doc)

        return 0

    sys.exit(main())
