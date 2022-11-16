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
TABLE_WLC_CLIENTS = 'WLC_CLIENTS'

# 保管する履歴
DEFAULT_WLC_MAX_HISTORY = 168   # 1時間に1回実行して7日分

logger = logging.getLogger(__name__)

#
# WLCに接続している無線クライアントに関する情報
#

def insert_wlc_clients(wlc_clients_list:list, timestamp:float, max_history:int=DEFAULT_WLC_MAX_HISTORY, table_name:str=TABLE_WLC_CLIENTS):
    """_summary_

    {
        'timestamp': float型 タイムスタンプ,
        'doc_data': [ {'mac_address': a.b.c.d, 'ap_name': ...}, {}, {}]
    }

    Args:
        wlc_clients_list (list): doc_dataとして格納する配列
        timestamp (float): 採取した時刻のタイムスタンプ
        max_history (int, optional): 蓄積する数 Defaults to DEFAULT_WLC_MAX_HISTORY.
        table_name (str, optional): テーブル名 Defaults to TABLE_WLC_CLIENTS.
    """

    # 格納するドキュメント
    doc = {}

    # タイムスタンプを付与
    doc['timestamp'] = timestamp

    # ドキュメントデータを付与
    doc['doc_data'] = wlc_clients_list

    # テーブルに格納
    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        table.insert(doc)

    # max_historyを超えた古いものを削除
    delete_old_wlc_clients(max_history)


def delete_old_wlc_clients(max_history:int, table_name:str=TABLE_WLC_CLIENTS):

    q = Query()

    # 降順のタイムスタンプの一覧を取得
    timestamps = get_wlc_clients_timestamps(table_name=table_name)

    # max_historyを超えたものを削除
    if len(timestamps) > max_history:
        should_be_deleted = timestamps[max_history:]
        with TinyDB(DB_PATH) as db:
            table = db.table(table_name)

            for ts in should_be_deleted:
                table.remove(q.timestamp == ts)


def get_wlc_clients_timestamps(table_name:str=TABLE_WLC_CLIENTS):

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)

        # timestampキーの一覧を取り出す
        timestamps = [doc['timestamp'] for doc in table.all()]

    # 降順にソートする
    timestamps.sort(reverse=True)

    return timestamps


def get_wlc_clients_dates(table_name:str=TABLE_WLC_CLIENTS):

    timestamps = get_wlc_clients_timestamps(table_name=table_name)

    # datetimeオブジェクトに変換
    datetimes = [datetime.fromtimestamp(ts) for ts in timestamps]

    # 分かりやすく日付の文字列に変換
    dates = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in datetimes]

    return dates


def get_wlc_clients_documents(table_name:str=TABLE_WLC_CLIENTS):
    """
    全てのドキュメントをタイムスタンプでソートして返却

    Args:
        table_name (str, optional): テーブル名. Defaults to TABLE_WLC_CLIENTS.

    Returns:
        list: ドキュメントのリスト
    """
    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        return sorted(table.all(), key=lambda d: d['timestamp'], reverse=True)


def get_wlc_clients_by_timestamp(timestamp:float, table_name:str=TABLE_WLC_CLIENTS):
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        return table.get(q.timestamp == timestamp)


if __name__ == '__main__':

    import sys
    from pprint import pprint

    logging.basicConfig(level=logging.INFO)

    def main():
        pprint(get_wlc_clients_dates())
        return 0

    sys.exit(main())
