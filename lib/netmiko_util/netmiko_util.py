#!/usr/bin/env python

#
# WLC接続用
#

# netmiko
# https://github.com/ktbyers/netmiko

# CiscoWlcSSH
# https://ktbyers.github.io/netmiko/docs/netmiko/cisco/cisco_wlc_ssh.html
# https://github.com/ktbyers/netmiko/blob/develop/netmiko/cisco/cisco_wlc_ssh.py

import logging
import re

# netmiko
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException

logger = logging.getLogger(__name__)


class CiscoWlcHandler:

    def __init__(self, ip:str, username:str, password:str) -> None:
        self.ip = ip
        self.username = username
        self.password = password

        # 暗黙のパラメータ
        self.port = 22
        self.device_type = 'cisco_wlc_ssh'
        self.conn_timeout = 10    # paramiko default 10
        self.banner_timeout = 15  # paramiko default 15

        # ConnectionHandlerインスタンス
        self.ch = None


    def __enter__(self):
        if self.ch is None:
            self.connect()
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        if self.ch is not None:
            self.ch.disconnect()
            self.ch = None


    def connect(self):
        if self.ch is None:
            args = {
                'ip': self.ip,
                'port': self.port,
                'username': self.username,
                'password': self.password,
                'device_type': 'cisco_wlc_ssh',
                #
                # pass to paramiko
                #
                'conn_timeout': self.conn_timeout,  # default 10
                'banner_timeout': self.banner_timeout,  # default 15
            }

            try:
                self.ch = ConnectHandler(**args)
                return self.ch
            except NetmikoAuthenticationException as e:
                logger.error('authentication failed.')
                raise e


    def get_wlc_clients(self):

        results = []

        # show client summaryを叩いてクライアントのMACアドレス情報を取得
        cmd_show_client_summary = 'show client summary'
        output = self.ch.send_command(cmd_show_client_summary)

        # 出力をパースしてクライアントリストを作成
        client_list = parse_wlc_show_client_summary(output)

        # MACアドレスを取り出して show client detail xx:xx:xx:xx:xx:xx コマンドを実行する
        for client in client_list:
            mac_address = client['mac_address']
            cmd_show_client_detail = f'show client detail {mac_address}'

            output = self.ch.send_command(cmd_show_client_detail)
            print(output)
            print('')

            # パース
            d = parse_wlc_show_client_detail(output)
            results.append(d)

        return results



def parse_wlc_show_client_summary(output: str) -> list:
    """
    WLCのshow client summary出力をパースする

    Args:
        lines (list): show client summaryの出力を行ごとにパースした{'mac_address', 'ap_name', 'protocol'}のリスト
    """

    re_marker = re.compile(r'([-]+\s+){10}[-]+')

    re_client = re.compile(
        r'(?P<mac_address>(?:[0-9a-fA-F]{2}\:){5}[0-9a-fA-F]{2})\s+(?P<ap_name>\S+)\s+\d+\s+\S+\s+\d+\s+\S+\s+(?P<protocol>802.11\S+\(.*\))\s+\d+'
    )

    # 結果を格納するリスト
    client_list = []

    # 処理中かどうか
    is_section = False

    # 行に分解して走査
    for line in output.splitlines():

        # print(line)

        # マーカー行を見つけるまで無用な情報をスキップする
        if not is_section:
            # この行が区切りかどうかを判定
            match = re_marker.search(line)
            if match:
                # マーカーを見つけた
                is_section = True
            # 次の行に移動
            continue

        # この行のクライアント情報を正規表現で抜き出す
        match = re_client.search(line)
        if match:
            d = {
                'mac_address': match.group('mac_address'),
                'ap_name': match.group('ap_name'),
                'protocol': match.group('protocol')
            }

            client_list.append(d)

            # この行の情報は取り込んだので次の行へ
            continue

        break

    return client_list


def parse_wlc_show_client_detail(output: str):

    regexp_dict = {
        # Client MAC Address............................... 04:03:d6:d8:57:5f
        'mac_address': re.compile(r'Client\s+MAC\s+Address(\s*)(\.)+\s+(?P<mac_address>(?:[0-9a-fA-F]{2}\:){5}[0-9a-fA-F]{2})(\s*)$', re.MULTILINE),

        # Client Username ................................. N/A
        'username': re.compile(r'Client\s+Username(\s*)(\.)+\s+(?P<username>\S+)(\s*)$', re.MULTILINE),

        # Hostname: .......................................
        'hostname': re.compile(r'Hostname\:(\s*)(\.)+\s+(?P<hostname>\S+)?(\s*)$', re.MULTILINE),

        # Device Type: .................................... NintendoWII
        'device_type': re.compile(r'Device\s+Type\:(\s*)(\.)+\s+(?P<device_type>\S+)?(\s*)$', re.MULTILINE),

        # AP MAC Address................................... 70:ea:1a:84:16:c0
        'ap_mac_address':
        re.compile(r'AP\s+MAC\s+Address(\s*)(\.)+\s+(?P<ap_mac_address>(?:[0-9a-fA-F]{2}\:){5}[0-9a-fA-F]{2})(\s*)$', re.MULTILINE),

        # AP Name.......................................... living-AP1815M
        'ap_name': re.compile(r'AP\s+Name(\s*)(\.)+\s+(?P<ap_name>.*)(\s*)$', re.MULTILINE),

        # Client State..................................... Associated
        'client_state': re.compile(r'Client\s+State(\s*)(\.)+\s+(?P<client_state>\S+)(\s*)$', re.MULTILINE),

        # Wireless LAN Network Name (SSID)................. taka 11ng
        'wireless_lan_network_name': re.compile(r'Wireless\s+LAN\s+Network\s+Name\s+\(SSID\)(\s*)(\.)+\s+(?P<wireless_lan_network_name>.*)(\s*)$', re.MULTILINE),

        # Connected For ................................... 4946 secs
        'connected_for': re.compile(r'Connected\s+For(\s*)(\.)+\s+(?P<connected_for>\d+)\s+secs(\s*)$', re.MULTILINE),

        # IP Address....................................... 192.168.122.107
        'ip_address': re.compile(r'IP\s+Address(\s*)(\.)+\s+(?P<ip_address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\s*)$', re.MULTILINE),

        # Gateway Address.................................. 192.168.122.1
        'gateway_address': re.compile(r'Gateway\s+Address(\s*)(\.)+\s+(?P<gateway_address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\s*)$', re.MULTILINE),

        # Netmask.......................................... 255.255.255.0
        'netmask': re.compile(r'Netmask(\s*)(\.)+\s+(?P<netmask>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\s*)$', re.MULTILINE)
    }

    result = {}
    for key, regexp in regexp_dict.items():
        match = regexp.search(output)
        if match:
            value = match.group(key)
        if not value:
            value = ''
        result[key] = value.strip()

    return result


if __name__ == '__main__':

    import argparse
    import os
    import sys

    from pprint import pprint

    #
    # libディレクトリをパスに加える
    #
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    lib_dir = os.path.join(app_dir, 'lib')

    if lib_dir not in sys.path:
        sys.path.append(lib_dir)

    from pyats_util import get_inventory

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true')
    args, _ = parser.parse_known_args()


    def test_parse_wlc_show_client_summary():
        path = os.path.join(os.path.dirname(__file__),
                            'show_client_summary.txt')
        with open(path) as f:
            cmd_output = f.read()

        client_list = parse_wlc_show_client_summary(cmd_output)
        # pprint(client_list)

        # 先頭3
        assert {'ap_name': 'living-AP1815M', 'mac_address': '04:03:d6:d8:57:5f', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '08:97:98:04:22:e4', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '20:df:b9:b4:bc:79', 'protocol': '802.11ac(5 GHz)'} in client_list
        # 最後3
        assert {'ap_name': 'ayane-CAP702I', 'mac_address': 'ee:e7:80:e3:c3:b2', 'protocol': '802.11n(5 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'f6:ff:cc:5f:51:68', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'fe:dd:b8:3f:de:59', 'protocol': '802.11ac(5 GHz)'} in client_list
        print('test_parse_wlc_show_client_summary() passed')


    def test_parse_wlc_show_client_detail():
        path = os.path.join(os.path.dirname(__file__),
                            'show_client_detail.txt')
        with open(path) as f:
            cmd_output = f.read()

        result = parse_wlc_show_client_detail(cmd_output)
        # pprint(result)

        assert result['ap_mac_address'] == '70:ea:1a:84:16:c0'
        assert result['ap_name'] == 'living-AP1815M'
        assert result['client_state'] == 'Associated'
        assert result['connected_for'] == '6842'
        assert result['device_type'] == 'NintendoWII'
        assert result['gateway_address'] == '192.168.122.1'
        assert result['ip_address'] == '192.168.122.107'
        assert result['mac_address'] == '04:03:d6:d8:57:5f'
        assert result['netmask'] == '255.255.255.0'
        assert result['username'] == 'N/A'
        assert result['wireless_lan_network_name'] == 'taka 11ng'
        print('test_parse_wlc_show_client_detail() passed')


    def test():
        test_parse_wlc_show_client_summary()
        test_parse_wlc_show_client_detail()
        return 0


    def main():

        if args.test:
            test()
            return 0

        # pyATSのテストベッドからwlcに関する情報を取得
        inventory = get_inventory('home.yaml', 'wlc')
        ip = inventory['ip']
        username = inventory['username']
        password = inventory['password']

        wlc = CiscoWlcHandler(ip, username, password)
        with wlc:
            clients_list = wlc.get_wlc_clients()
        pprint(clients_list)
        return 0

    sys.exit(main())
