#!/usr/bin/env python

import logging
import os
import sys

from datetime import datetime
from pprint import pprint

#
# tinydb
#
from tinydb import Query, TinyDB

# JSONファイル
DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, 'db.json')

# テーブルの種類
TABLE_PYATS = 'PYATS'

DEFAULT_DEVICE_MAX_HISTORY = 10

logger = logging.getLogger(__name__)

#
# pyATS取得情報
#

def insert_device_data(device_name:str, doc_type:str, doc_data:dict, timestamp:float, max_history=DEFAULT_DEVICE_MAX_HISTORY):
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


def get_documents(doc_type:str):
    """
    ドキュメントタイプで検索し、タイムスタンプでソートして返却

    Args:
        doc_type (str): ドキュメントタイプ

    Returns:
        list: 見つかったドキュメントのリスト
    """
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(TABLE_PYATS)
        docs = table.search((q.doc_type == doc_type))

    if docs:
        return sorted(docs, key=lambda d: d['timestamp'], reverse=True)

    return []


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
    dates = [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in datetimes]

    return dates


def insert_device_mac_address_table(device_name:str, mac_address_table:dict, timestamp:float, max_history=DEFAULT_DEVICE_MAX_HISTORY):
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


def get_mac_address_table():
    """
    'mac_address_table' をタイムスタンプでソートして返却

    Args:

    Returns:
        list: 見つかったドキュメントのリスト
    """
    return get_documents('mac_address_table')



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


def dump():
    devices = ['c3560c-12pc-s', 'c2960cx-8pc']

    try:
        for device_name in devices:
            docs = get_device_mac_address_table(device_name=device_name)
            for d in docs:
                pprint(d)
    except (BrokenPipeError, IOError):
        # lessにパイプしたときのBrokenPipeError: [Errno 32] Broken pipeを避ける
        sys.stderr.close()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':

    import argparse

    logging.basicConfig(level=logging.INFO)


    def test_insert_device_data():
        device_name = os.uname()[1]

        doc_data = {
            'test_key': 'test_data'
        }

        timestamp = datetime.now().timestamp()

        insert_device_data(device_name=device_name, doc_type='test', doc_data=doc_data, timestamp=timestamp, max_history=DEFAULT_DEVICE_MAX_HISTORY)

        docs = get_device_documents(device_name=device_name, doc_type='test')

        print(f'numbered of stored data is {len(docs)}')
        for doc in docs:
            print(doc)

    #
    # main
    #

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true', default=False, help='test')
    parser.add_argument('-d', '--dump', action='store_true', default=False, help='dump all data')
    args = parser.parse_args()

    def main():
        if args.test:
            test_insert_device_data()
            return 0

        if args.dump:
            dump()
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
