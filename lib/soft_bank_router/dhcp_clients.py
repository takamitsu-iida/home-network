#!/usr/bin/env python

import logging
import os
import sys
import re

from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth

#
# libディレクトリをパスに加える
#
app_dir = os.path.join(os.path.dirname(__file__), '../..')
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# データベース操作関数 lib/db_util/db_util.py
from db_util import insert_dhcp_clients

# pyats操作関数 lib/pyats_util/pyats_util.py
from pyats_util import get_inventory

logger = logging.getLogger(__name__)


def get_html(ip: str, username: str, password: str) -> str:
    """_summary_

    Args:
        ip (str): ソフトバンク光ルータのIPアドレス
        username (str): 接続ユーザ名
        password (str): 接続パスワード

    Returns:
        str: HTMLコンテンツ
    """
    # ベーシック認証情報を作成
    auth = HTTPBasicAuth(username, password)

    # DHCPクライアントを表示するURL
    url = f'http://{ip}/P_Hinfo_dhcpclientslist.html'

    # ページを取得
    r = requests.get(url, auth=auth)

    # 200以外は例外を出して終了
    r.raise_for_status()

    # 画面表示で確認
    # print(r.text)

    # ファイルに保存して確認
    # r.encoding = r.apparent_encoding
    # html_file = os.path.join(os.path.dirname(__file__), 'scraped.html')
    # with open(html_file, mode='w') as f:
    #     f.write(r.text)

    return r.text


def scrape_html(html_content: str) -> list:
    """
    HTMLコンテンツをスクレイピングしてDHCPクライアント情報を取り出す

    注意
    DHCPの払い出し情報はjavascriptでレンダリングしているので、HTMLタグの中に情報は埋め込まれていない。
    <SCRIPT>タグの中のjavascriptのコードをスクレイピングする。

    Args:
        html_content (str): requestsで取得したHTMLコンテンツ

    Returns:
        list: 辞書型を格納したリスト。例 [{'ip': '192.168.122.106', 'mac': '28:84:fa:ea:5f:0c'}, {}, {}...]
    """

    # このjavascriptの関数から正規表現を使ってほしい部分を取り出す
    #
    # function PrintInfo()
    # {
    #         var cf = document.forms[0];
    #         var i=0, j=0, m=0, n=0;
    #         //foxconn add start by sunny,2009/03/20
    #         var space_count;
    #         //foxconn add end by sunny,2009/03/20
    #         var past_length_ip, past_length_mac;
    #         var counter_ip=0, counter_mac=0;
    #
    #         cf.infoarea.value = "";
    #
    #         cf.IP.value = "192.168.122.106 192.168.122.107 192.168.122.109 192.168.122.111 192.168.122.112 192.168.122.114 192.168.122.115 192.168.122.116 192.168.122.118 192.168.122.119 192.168.122.156 192.168.122.120 192.168.122.121 192.168.122.122 192.168.122.123 192.168.122.169 192.168.122.159 192.168.122.160 192.168.122.172 192.168.122.174";
    #         cf.MAC.value = "28:84:fa:ea:5f:0c 04:03:d6:d8:57:5f 3c:22:fb:7b:85:0e 2e:14:db:b8:9b:d8 fe:dd:b8:3f:de:59 44:65:0d:da:2a:f5 68:84:7e:87:04:be ee:e7:80:e3:c3:b2 7e:87:0b:67:17:e2 20:df:b9:b4:bc:79 38:1a:52:5b:42:15 a4:5e:60:e4:1a:dd c6:78:ad:69:2d:fd 12:87:66:76:e7:7d 26:67:ca:be:bc:c9 84:5c:f3:48:ff:30 90:9a:4a:d6:bb:b9 08:97:98:04:22:e4 f6:ff:cc:5f:51:68 50:eb:f6:95:8b:37";

    re_ip = re.compile(r'cf\.IP\.value = "(.*)";', re.MULTILINE)
    re_mac = re.compile(r'cf\.MAC\.value = "(.*)";', re.MULTILINE)

    ip_list = []
    match = re.search(re_ip, html_content)
    if match:
        ip = match.group(1)
        ip_list = ip.split()

    mac_list = []
    match = re.search(re_mac, html_content)
    if match:
        mac = match.group(1)
        mac_list = mac.split()

    result_list = []
    for ip, mac in zip(ip_list, mac_list):
        result_list.append({'ip': ip, 'mac': mac.upper()})

    # pprint(result_list)
    #
    # [{'ip': '192.168.122.106', 'mac': '28:84:FA:EA:5F:0C'},
    #  {'ip': '192.168.122.107', 'mac': '04:03:D6:D8:57:5F'},
    #  {'ip': '192.168.122.109', 'mac': '3C:22:FB:7B:85:0E'},
    #  {'ip': '192.168.122.111', 'mac': '2E:14:DB:B8:9B:D8'},

    return result_list


def update_db():  ############# 引数にip, username, passwordを渡すように変更

    # pyATSのテストベッドからソフトバンク光ルータに関する情報を取得
    inventory = get_inventory('home.yaml', 'softbank-router')
    if inventory is None:
        return

    ip = inventory.get('ip')
    username = inventory.get('username')
    password = inventory.get('password')

    # 現在時刻
    timestamp = datetime.now().timestamp()

    # HTMLを取得する
    html_content = get_html(ip=ip, username=username, password=password)

    # 取得したHTMLをスクレイピング
    dhcp_clients = scrape_html(html_content=html_content)

    # データベースに格納
    insert_dhcp_clients(dhcp_clients_list=dhcp_clients, timestamp=timestamp)

    return dhcp_clients


if __name__ == '__main__':

    import argparse
    import time
    from pprint import pprint

    import daemon
    import schedule

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='dhcp_clients.py')
    parser.add_argument('-d',
                        '--daemon',
                        action='store_true',
                        default=False,
                        help='Daemon')

    args = parser.parse_args()

    def main():

        if args.daemon:

            # 毎時update_db()を実行する
            schedule.every(1).hours.do(update_db)

            # デーモンを作成して、
            with daemon.DaemonContext(stdout=sys.stdout):
                while True:
                    schedule.run_pending()
                    time.sleep(1)

        else:
            # データベースをアップデートして、
            dhcp_clients = update_db()

            # 戻り値を画面表示して終了
            pprint(dhcp_clients)

        return 0

    sys.exit(main())