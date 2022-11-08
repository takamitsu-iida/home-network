
#!/usr/bin/env python

import os

from datetime import datetime

#
# tinydb
#
from tinydb import TinyDB, Query

DB_DIR = os.path.join(os.path.dirname(__file__), 'tinydb')
DB_PATH = os.path.join(DB_DIR, 'db.json')

# ディレクトリを作成
os.makedirs(DB_DIR, exist_ok=True)


def insert_data(device_name:str, doc_type:str, doc_data:dict, timestamp:float, max_history=10):
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
        max_history (int, optional): 何個まで保存するか Defaults to 10.
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
        return sorted(datas, key=lambda d: d['timestamp'])

    return []


def get_stored_dates(device_name:str, doc_type:str):

    # 名前でドキュメントを取り出す
    docs = get_documents_by_name(device_name, doc_type)

    # timestampキーの一覧を取り出す
    timestamps = [doc['timestamp'] for doc in docs]

    # datetimeオブジェクトに変換
    datetimes = [datetime.fromtimestamp(ts) for ts in timestamps]

    # 分かりやすく日付の文字列に変換
    dates = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in datetimes]

    return dates


def insert_mac_address_table(device_name:str, mac_address_table:dict, timestamp:float, max_history=10):
    """
    parse('show mac address-table')をデータベースに保存する。

    Args:
        device_name (str): 学習した装置の名前
        mac_address_table (dict): parse()したMACアドレステーブル
        timestamp (float): 実行した時点のタイムスタンプ
        max_history (int, optional): 何個まで保存するか Defaults to 10.
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

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='../lab.yml')
    args, _ = parser.parse_known_args()

    #
    # pyATS
    #
    from genie.testbed import load
    from genie.ops.utils import get_ops

    def _get_intf_info(testbed):

        testbed = load(args.testbed)

        uut = testbed.devices['uut']

        # connect
        uut.connect()

        # learn all interfaces
        Interface = get_ops('interface', uut)
        intf = Interface(device=uut)
        intf.learn()

        # disconnect
        if uut.is_connected():
            uut.disconnect()

        # 学習した結果の辞書型はinfoキーで入手可能
        # pprint(intf.info)
        #
        # {'GigabitEthernet1': {},
        #  'GigabitEthernet2': {},
        #  'GigabitEthernet3': {},

        return uut.name, intf.info

    # 全装置で共通の実行時のタイムスタンプ、
    timestamp = datetime.now().timestamp()

    # インタフェースを学習
    device_name, intf_info = _get_intf_info(args.testbed)

    # dbに格納
    insert_intf_info(device_name, intf_info, timestamp, max_history=2)

    # タイムスタンプの一覧を日付に変換して取得
    dates = get_stored_dates(device_name)

    # 表示
    print(f'stored dates for {device_name} = {dates}')

    # デバイスに関する情報を取り出す
    datas = get_intf_info_by_name(device_name)

    for d in datas:
        print(d['timestamp'])
