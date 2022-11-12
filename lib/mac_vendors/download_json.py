#!/usr/bin/env python

# MACアドレスのベンダーコードのJSONデータを取得してtinydbに格納する
#
# 参照
# https://maclookup.app/downloads/json-database
#

import logging
import os
import sys
from dateutil.parser import parse

import requests

# IPv6での接続に問題がありそうなので、IPv6での接続を抑止する
requests.packages.urllib3.util.connection.HAS_IPV6 = False

#
# lib/db_util/db_util.py
#
app_dir = os.path.join(os.path.dirname(__file__), '../..')
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

from db_util import insert_mac_vendors
from db_util import get_mac_vendors_timestamp

# ダウンロードリンク
URL = 'https://maclookup.app/downloads/json-database/get-db'

logger = logging.getLogger(__name__)


def get_last_modified(url:str, requests_options={}) -> float:

    logger.info(f'head {url}')

    headers = {'content-type': 'application/json'}

    r = requests.head(url, headers=headers, **requests_options)

    # print(r.headers)
    # {'Date': 'Fri, 11 Nov 2022 08:28:54 GMT',
    #  'Content-Type': 'application/octet-stream',
    #  'Connection': 'keep-alive', 'Cache-Control':
    #  'public, max-age=3600',
    #  'Content-Description': 'File Transfer',
    #  'Content-Disposition': 'attachment; filename="mac-vendors-export.json"',
    #  'Content-Transfer-Encoding': 'binary',
    #  'X-Srv': 'MAC Lookup Frontend [v16.8.10]',
    #  'X-Srv-Id': '3c903eb5-9552-4dd0-bd7f-2db1f49cb078',
    #  'Last-Modified': 'Fri, 11 Nov 2022 07:58:52 GMT',
    #  'CF-Cache-Status': 'HIT',

    last_modified = r.headers.get('Last-Modified', None)
    if last_modified is None:
        return None

    dt = parse(last_modified)
    ts = dt.timestamp()
    return ts


def get_mac_vendors_list(url:str, requests_options={}) -> list:

    logger.info(f'get {url}')

    headers = {'content-type': 'application/json'}

    r = requests.get(url, headers=headers, **requests_options)

    # print(r.headers)
    # {'Date': 'Sun, 06 Nov 2022 07:51:56 GMT',
    #  'Content-Type': 'application/octet-stream',
    #  'Connection': 'keep-alive',
    #  'Cache-Control': 'public, max-age=3600',
    #  'Content-Description': 'File Transfer',
    #  'Content-Disposition': 'attachment; filename="mac-vendors-export.json"',
    #  'Content-Transfer-Encoding': 'binary',
    #  'X-Srv': 'MAC Lookup Frontend [v16.8.10]',
    #  'X-Srv-Id': '3c903eb5-9552-4dd0-bd7f-2db1f49cb078',
    #  'Last-Modified': 'Sun, 06 Nov 2022 07:42:04 GMT',
    #  'CF-Cache-Status': 'HIT',

    # ファイル名が必要な場合
    # content_disposition = r.headers.get('Content-Disposition', 'filename="downloaded.json"')
    # filename = content_disposition.split('filename=')[1]
    # filename = filename.strip('"')
    # filename = filename.strip("'")

    r.raise_for_status()
    data = r.json()

    #
    # [{"macPrefix":"00:00:0C",
    #   "vendorName":"Cisco Systems, Inc",
    #   "private":false,
    #   "blockType":"MA-L",
    #   "lastUpdate":"2015/11/17"},
    #

    logger.info(f'{len(data)} mac vendors downloaded.')

    return data


def update_db():

    requests_options = {'timeout': 10}

    # headメソッドを使って 'Last-Modified' の情報を取得する
    timestamp = get_last_modified(URL, requests_options=requests_options)
    logger.info(f'current timestamp is {timestamp}')

    do_download = False

    # データベースに格納されているタイムスタンプを取得
    stored_timestamp = get_mac_vendors_timestamp()
    if stored_timestamp is None:
        logger.info('no data in database, try to download.')
        do_download = True
    else:
        logger.info(f'stored timestamp is {stored_timestamp}')
        if timestamp > stored_timestamp:
            logger.info(f'new data found, try to download.')
            do_download = True
        else:
            logger.info(f'download skipped, stored data is the newest.')

    if do_download:
        # ダウンロードして
        mac_vendors_list = get_mac_vendors_list(URL, requests_options=requests_options)

        insert_mac_vendors(mac_vendors_list=mac_vendors_list, timestamp=timestamp)


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    from db_util import get_mac_vendors_all
    from db_util import search_mac_vendors

    def main():

        # timestamp = get_last_modified(URL, requests_options={'timeout': 10})
        # print(timestamp)

        # data = get_mac_vendors_list(URL, requests_options={'timeout': 10})
        # print(data)

        # from db_util import delete_documents_by_name
        # delete_documents_by_name(device_name=os.uname()[1], doc_type=DOC_TYPE)

        # データベースをアップデートする
        update_db()

        # データベースから最新を取得する
        mac_vendors_list = get_mac_vendors_all()

        # このリストをpythonで検索
        query = '00:00:0C'
        answer = list(filter(lambda d: d['macPrefix'] == query, mac_vendors_list))
        if len(answer) > 0:
            vendor_name = answer[0].get('vendorName')
            print(f'{query} is {vendor_name}')

        print(search_mac_vendors('00:00:0C'))

        return 0

    sys.exit(main())
