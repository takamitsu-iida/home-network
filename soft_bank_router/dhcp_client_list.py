#!/usr/bin/env python

import logging
import re

from pprint import pprint

import requests
from requests.auth import HTTPBasicAuth

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


if __name__ == '__main__':

    import sys

    logging.basicConfig(level=logging.INFO)

    USERNAME = 'user'
    PASSWORD = 'user'

    auth = HTTPBasicAuth(USERNAME, PASSWORD)

    URL = 'http://192.168.122.1/P_Hinfo_dhcpclientslist.html'

    def main():

        r = requests.get(URL, auth=auth)

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
        script = ''
        for s in scripts:
            script += s.text
        # print(script)

        # 正規表現で取り出す
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