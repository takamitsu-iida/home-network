#!/usr/bin/env python

import logging
import os
import re
import sys

from pprint import pprint

app_dir = os.path.join(os.path.dirname(__file__), '../..')
lib_dir = os.path.join(app_dir, 'lib')
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

#
# import requests
#
import requests
from requests.auth import HTTPBasicAuth

#
# import BeautifulSoup
#
from bs4 import BeautifulSoup

#
# IPアドレス、ユーザ名、パスワード等のインベントリ情報はテストベッドファイルに記載
#
from genie.testbed import load
from pyats.utils.secret_strings import to_plaintext

#
# lib/pyats_util/pyats_util.py
#
from pyats_util import get_inventory


logger = logging.getLogger(__name__)


if __name__ == '__main__':

    import sys

    logging.basicConfig(level=logging.INFO)

    def main():

        inventory = get_inventory('home.yaml', 'softbank-router')
        if inventory is None:
            return 0

        ip = inventory.get('ip')
        username = inventory.get('username')
        password = inventory.get('password')

        auth = HTTPBasicAuth(username, password)

        url = f'http://{ip}/P_Hinfo_dhcpclientslist.html'

        r = requests.get(url, auth=auth)

        # 200以外は例外を出して終了
        r.raise_for_status()

        # bs4にHTMLコンテンツを渡す
        soup = BeautifulSoup(r.content, 'html.parser')

        #
        # DHCPの払い出し情報はjavascriptでレンダリングしているので、HTMLタグの中に情報は埋め込まれていない
        # <SCRIPT>タグの中のjavascriptのコードをスクレイピングする
        #

        # <SCRIPT>タグを全て取り出して結合する
        scripts = soup.find_all('script')
        script = '\n'.join([str(s) for s in scripts])

        # print(script)
        #
        # 正規表現を使ってほしい部分を取り出す
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
        match = re.search(re_ip, script)
        if match:
            ip = match.group(1)
            ip_list = ip.split()

        mac_list = []
        match = re.search(re_mac, script)
        if match:
            mac = match.group(1)
            mac_list = mac.split()

        result_list = []
        for ip, mac in zip(ip_list, mac_list):
            result_list.append({
                'ip': ip,
                'mac': mac
            })

        pprint(result_list)

        return 0

    sys.exit(main())