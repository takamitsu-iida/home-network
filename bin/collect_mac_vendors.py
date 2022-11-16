#!/usr/bin/env python

# MACアドレスのベンダーコードのJSONデータを取得してtinydbに格納する
#
# 参照
# https://maclookup.app/downloads/json-database
#

import argparse
import logging
import os
import sys

from pprint import pprint

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/db_util
from db_util import insert_mac_vendors, get_mac_vendors_all, get_mac_vendors_timestamp, search_mac_vendors

# lib/mac_vendors_util
from mac_vendors_util import get_mac_vendors_list, get_last_modified

logger = logging.getLogger(__name__)


def update_db():

    requests_options = {'timeout': 10}

    # headメソッドを使って 'Last-Modified' の情報を取得する
    timestamp = get_last_modified(requests_options=requests_options)
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
        mac_vendors_list = get_mac_vendors_list(
            requests_options=requests_options)

        # データベースに格納する
        insert_mac_vendors(mac_vendors_list=mac_vendors_list,
                           timestamp=timestamp)


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dump', action='store_true')
    parser.add_argument('-u', '--update', action='store_true')
    parser.add_argument('-s', '--search', dest='search', help='search MAC address', type=str)
    args, _ = parser.parse_known_args()

    def main():

        if args.dump:
            # データベースから取得する
            mac_vendors_list = get_mac_vendors_all()
            try:
                pprint(mac_vendors_list)
            except (BrokenPipeError, IOError):
                # lessにパイプしたときのBrokenPipeError: [Errno 32] Broken pipeを避ける
                sys.stderr.close()
            except KeyboardInterrupt:
                pass
            return 0

        if args.search:
            mac_address = args.search.upper()
            searched = search_mac_vendors(mac_address=mac_address)
            print(searched)
            return 0

        if args.update:
            # データベースをアップデートする
            update_db()
            return 0

        return 0

    sys.exit(main())
