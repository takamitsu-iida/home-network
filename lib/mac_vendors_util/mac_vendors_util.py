#!/usr/bin/env python

# MACアドレスのベンダーコードのJSONデータを取得してJSONファイルに保存する
#
# 参照
# https://maclookup.app/downloads/json-database

import json
import logging
import os
from dateutil.parser import parse

import requests

# IPv6での接続に問題がありそうなので、IPv6での接続を抑止する
requests.packages.urllib3.util.connection.HAS_IPV6 = False

# ダウンロードリンク
URL = 'https://maclookup.app/downloads/json-database/get-db'

logger = logging.getLogger(__name__)


def get_last_modified(url: str = URL, requests_options={}) -> float:

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


def get_mac_vendors_list(url: str = URL, requests_options={}, save=False) -> list:

    logger.info(f'get {url}')

    headers = {'content-type': 'application/json'}

    r = requests.get(url, headers=headers, **requests_options)

    r.raise_for_status()

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

    data = r.json()

    # pprint(data)
    #
    # [{"macPrefix":"00:00:0C",
    #   "vendorName":"Cisco Systems, Inc",
    #   "private":false,
    #   "blockType":"MA-L",
    #   "lastUpdate":"2015/11/17"},

    logger.info(f'{len(data)} mac vendors downloaded.')

    if save:
        # ファイル名をヘッダ情報から取得、ヘッダに含まれない場合はdownloaded.jsonとする
        content_disposition = r.headers.get('Content-Disposition', 'filename="downloaded.json"')
        filename = content_disposition.split('filename=')[1]
        filename = filename.strip('"')
        filename = filename.strip("'")

        json_dir = os.path.join(os.path.dirname(__file__), 'json')
        json_path = os.path.join(json_dir, filename)

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

    # このリストをmacPrefixキーの値でソートしてから返却する
    # return sorted(data, key=lambda x: x.get('macPrefix', ''))
    return data


def load_from_file(filename:str ='mac-vendors-export.json'):
    json_dir = os.path.join(os.path.dirname(__file__), 'json')
    json_path = os.path.join(json_dir, filename)

    with open(json_path) as f:
        data = json.load(f)

    return data


if __name__ == '__main__':

    import argparse
    import sys

    from pprint import pprint

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dump', action='store_true')
    parser.add_argument('-g', '--get', action='store_true')
    args, _ = parser.parse_known_args()

    def main():
        # --dump はJSONファイルをダンプ
        if args.dump:
            data = load_from_file()
            try:
                pprint(data)
            except (BrokenPipeError, IOError):
                sys.stderr.close()
            except KeyboardInterrupt:
                pass
            return 0

        # --getはサイトからダウンロードして、ファイルに保存
        if args.get:
            get_mac_vendors_list(requests_options={'timeout': 10}, save=True)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
