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
TABLE_DHCP_CLIENTS = 'DHCP_CLIENTS'

# 保管する履歴
DEFAULT_DHCP_MAX_HISTORY = 168   # 1時間に1回実行して7日分

logger = logging.getLogger(__name__)

#
# DHCPクライアント情報
#

def insert_dhcp_clients(dhcp_clients_list:list, timestamp:float, max_history:int=DEFAULT_DHCP_MAX_HISTORY, table_name:str=TABLE_DHCP_CLIENTS):
    """
    DHCPクライアントの情報をテーブルに格納する

    {
        'timestamp': float型タイムスタンプ,
        'doc_data': [ {'ip': a.b.c.d, 'mac': AA:BB:CC:DD:EE:FF}, {}, {}],
    }

    Args:
        dhcp_clients_list (list): doc_dataとして格納する配列
        timestamp (float): 採取した時刻のタイムスタンプ
        max_history (int, optional): 蓄積する数 Defaults to DEFAULT_DHCP_MAX_HISTORY.
        table_name (str, optional): テーブル名 Defaults to TABLE_DHCP_CLIENTS.
    """

    # 格納するドキュメント
    doc = {}

    # タイムスタンプを付与
    doc['timestamp'] = timestamp

    # ドキュメントデータを付与
    doc['doc_data'] = dhcp_clients_list

    # テーブルに格納
    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        table.insert(doc)

    # max_historyを超えた古いものを削除
    delete_old_dhcp_clients(max_history)


def delete_old_dhcp_clients(max_history:int, table_name:str=TABLE_DHCP_CLIENTS):

    q = Query()

    # 降順のタイムスタンプの一覧を取得
    timestamps = get_dhcp_clients_timestamps(table_name=table_name)

    # max_historyを超えたものを削除
    if len(timestamps) > max_history:
        should_be_deleted = timestamps[max_history:]
        with TinyDB(DB_PATH) as db:
            table = db.table(table_name)

            for ts in should_be_deleted:
                table.remove(q.timestamp == ts)


def get_dhcp_clients_timestamps(table_name:str=TABLE_DHCP_CLIENTS):

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)

        # timestampキーの一覧を取り出す
        timestamps = [doc['timestamp'] for doc in table.all()]

    # 降順にソートする
    timestamps.sort(reverse=True)

    return timestamps


def get_dhcp_clients_dates(table_name:str=TABLE_DHCP_CLIENTS):

    timestamps = get_dhcp_clients_timestamps(table_name=table_name)

    # datetimeオブジェクトに変換
    datetimes = [datetime.fromtimestamp(ts) for ts in timestamps]

    # 分かりやすく日付の文字列に変換
    dates = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in datetimes]

    return dates



def get_dhcp_clients_documents(table_name:str=TABLE_DHCP_CLIENTS):
    """
    全てのドキュメントをタイムスタンプでソートして返却

    Args:
        table_name (str, optional): テーブル名. Defaults to TABLE_DHCP_CLIENTS.

    Returns:
        list: ドキュメントのリスト
    """
    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        return sorted(table.all(), key=lambda d: d['timestamp'], reverse=True)


def get_dhcp_clients_by_mac(mac_address:str, table_name:str=TABLE_DHCP_CLIENTS):

    # 大文字に変換
    mac_address = mac_address.upper()

    results = []

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        # tinydbではドキュメントの一部を取り出すのは困難なので全てのドキュメントを確認する
        for doc in table.all():
            timestamp = doc['timestamp']
            dhcp_clients_list = doc['doc_data']
            filtered = list(filter(lambda d: d['mac'] == mac_address, dhcp_clients_list))
            if filtered:
                # 先頭一つを取り出す
                filtered = filtered[0]
                filtered.update({'timestamp': timestamp})
                results.append(filtered)

    return results


def get_dhcp_clients_by_timestamp(timestamp:float, table_name:str=TABLE_DHCP_CLIENTS):
    q = Query()

    with TinyDB(DB_PATH) as db:
        table = db.table(table_name)
        return table.get(q.timestamp == timestamp)


def get_dhcp_clients_diff(table_name:str=TABLE_DHCP_CLIENTS):

    # このタイムスタンプは新しい順に並んでいる
    timestamps = get_dhcp_clients_timestamps(table_name=table_name)

    # 最小で2個のデータがないと比較できない
    if len(timestamps) < 2:
        return None

    timestamps_before = timestamps[1:]  # リストを右に一つずらす
    timestamps.pop() # 一番右を削除してリストの要素数を揃える

    results = []

    for ts_after, ts_before in zip(timestamps, timestamps_before):
        after_doc = get_dhcp_clients_by_timestamp(ts_after)
        before_doc = get_dhcp_clients_by_timestamp(ts_before)

        after_data = after_doc.get('doc_data', [])
        before_data = before_doc.get('doc_data', [])

        # ひとつ前と比較して違いがあれば
        if after_data != before_data:

            diff = {}
            diff['timestamp_before'] = ts_before
            diff['timestamp_after'] = ts_after

            added = [d for d in after_data if d not in before_data]
            diff['add'] = added

            deleted = [p for p in before_data if p not in after_data]
            diff['delete'] = deleted

            results.append(diff)

    return results


if __name__ == '__main__':

    import argparse
    import sys

    from pprint import pprint

    logging.basicConfig(level=logging.INFO)


    def test_dhcp_clients_diff():
        diff_list = get_dhcp_clients_diff()
        for diff in diff_list:
            ts_after = diff.get('timestamp_after')
            ts_before = diff.get('timestamp_before')

            dt_after = datetime.fromtimestamp(ts_after).strftime('%Y-%m-%d %H:%M:%S')
            dt_before = datetime.fromtimestamp(ts_before).strftime('%Y-%m-%d %H:%M:%S')

            print(f'{dt_after} is different from {dt_before}')

            added = diff.get('add')
            if added:
                print(f'+ {added}')

            deleted = diff.get('delete')
            if deleted:
                print(f'- {deleted}')

            print('')


    def test_dhcp_clients_table():
        table_name = 'TEST_DHCP_CLIENTS'

        dhcp_clients_list = [
            {'ip': '192.168.122.106', 'mac': '28:84:FA:EA:5F:0C'},
            {'ip': '192.168.122.107', 'mac': '04:03:D6:D8:57:5F'},
            {'ip': '192.168.122.109', 'mac': '3C:22:FB:7B:85:0E'}
        ]

        with TinyDB(DB_PATH) as db:
            db.drop_table(table_name)

        timestamp = datetime.now().timestamp()
        insert_dhcp_clients(dhcp_clients_list=dhcp_clients_list, timestamp=timestamp, max_history=100, table_name=table_name)

        timestamp = datetime.now().timestamp()
        insert_dhcp_clients(dhcp_clients_list=dhcp_clients_list, timestamp=timestamp, max_history=100, table_name=table_name)

        docs = get_dhcp_clients_documents(table_name=table_name)

        assert 2 == len(docs)

        searched = get_dhcp_clients_by_mac(mac_address='28:84:FA:EA:5F:0C', table_name=table_name)
        print(searched)

        with TinyDB(DB_PATH) as db:
            db.drop_table(table_name)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--status', action='store_true', help='show table status')
    parser.add_argument('-d', '--diff', action='store_true', help='show table diff')
    args, _ = parser.parse_known_args()

    def main():
        if args.status:
            dates = get_dhcp_clients_dates()
            print(f'number of entries: {len(dates)}')
            pprint(get_dhcp_clients_dates())
            return 0

        if args.diff:
            test_dhcp_clients_diff()
            return 0

        parser.print_help()

    sys.exit(main())
