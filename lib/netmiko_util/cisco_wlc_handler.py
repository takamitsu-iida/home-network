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

    def __init__(self, ip:str, username:str, password:str, log_stdout=True) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.log_stdout = log_stdout

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
                'banner_timeout': self.banner_timeout,  # default 15,
                'verbose': False
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
            if self.log_stdout:
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
        'mac_address': re.compile(r'Client MAC Address( *)(\.)+( +)(?P<mac_address>(?:[0-9a-fA-F]{2}\:){5}[0-9a-fA-F]{2})( *)$', re.MULTILINE),

        # Client Username ................................. N/A
        'username': re.compile(r'Client Username( *)(\.)+( +)(?P<username>\S+)( *)$', re.MULTILINE),

        # Hostname: .......................................
        'hostname': re.compile(r'Hostname:(\s*)(\.)+ +(?P<hostname>\S.*)$', re.MULTILINE),

        # Device Type: .................................... NintendoWII
        # Device Type: .................................... iPad 6th Gen
        # Device Type: .................................... iPhone 8
        'device_type': re.compile(r'Device Type:( *)(\.)+( +)(?P<device_type>\S.*)?$', re.MULTILINE),

        # AP MAC Address................................... 70:ea:1a:84:16:c0
        'ap_mac_address':
        re.compile(r'AP MAC Address( *)(\.)+( +)(?P<ap_mac_address>(?:[0-9a-fA-F]{2}\:){5}[0-9a-fA-F]{2})( *)$', re.MULTILINE),

        # AP Name.......................................... living-AP1815M
        'ap_name': re.compile(r'AP Name( *)(\.)+( +)(?P<ap_name>\S.*)$', re.MULTILINE),

        # Client State..................................... Associated
        'client_state': re.compile(r'Client State( *)(\.)+( +)(?P<client_state>\S.*)$', re.MULTILINE),

        # Wireless LAN Network Name (SSID)................. taka 11ng
        'wireless_lan_network_name': re.compile(r'Wireless LAN Network Name \(SSID\)( *)(\.)+( +)(?P<wireless_lan_network_name>\S.*)$', re.MULTILINE),

        # Connected For ................................... 4946 secs
        'connected_for': re.compile(r'Connected For( *)(\.)+( +)(?P<connected_for>\d+)( +)secs( *)$', re.MULTILINE),

        # IP Address....................................... 192.168.122.107
        'ip_address': re.compile(r'IP Address( *)(\.)+( +)(?P<ip_address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\s*)$', re.MULTILINE),

        # Gateway Address.................................. 192.168.122.1
        'gateway_address': re.compile(r'Gateway Address( *)(\.)+( +)(?P<gateway_address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\s*)$', re.MULTILINE),

        # Netmask.......................................... 255.255.255.0
        'netmask': re.compile(r'Netmask( *)(\.)+( +)(?P<netmask>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})( *)$', re.MULTILINE)
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

    # テスト用にpyATSのテストベッドからWLCのインベントリ情報を取りたいのでlibディレクトリをパスに加える
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    lib_dir = os.path.join(app_dir, 'lib')
    if lib_dir not in sys.path:
        sys.path.append(lib_dir)

    from pyats_util import get_testbed_from_file, get_inventory

    logging.basicConfig(level=logging.INFO)

    def test_parse_wlc_show_client_summary():
        filename = 'show_client_summary.txt'
        outputs_dir = os.path.join(os.path.dirname(__file__), 'wlc_outputs')
        path = os.path.join(outputs_dir, filename)

        with open(path) as f:
            cmd_output = f.read()

        client_list = parse_wlc_show_client_summary(cmd_output)
        # pprint(client_list)

        # 先頭3
        assert {'ap_name': 'living-AP1815M', 'mac_address': '04:03:d6:d8:57:5f', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '08:97:98:04:22:e4', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '20:df:b9:b4:bc:79', 'protocol': '802.11ac(5 GHz)'} in client_list
        # 最後3
        assert {'ap_name': 'ayane-CAP702I', 'mac_address': 'ee:e7:80:e3:c3:b2', 'protocol': '802.11n(5 GHz)'}
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'f6:ff:cc:5f:51:68', 'protocol': '802.11ac(5 GHz)'}
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'fe:dd:b8:3f:de:59', 'protocol': '802.11ac(5 GHz)'}
        print('test_parse_wlc_show_client_summary() passed')


    def test_parse_wlc_show_client_detail():
        filename = 'show_client_detail.txt'  # 'show_client_detail_eee780e3c3b2.txt'
        outputs_dir = os.path.join(os.path.dirname(__file__), 'wlc_outputs')
        path = os.path.join(outputs_dir, filename)

        with open(path) as f:
            cmd_output = f.read()

        result = parse_wlc_show_client_detail(cmd_output)
        pprint(result)

        assert result['ap_mac_address'] == '70:ea:1a:84:16:c0'
        assert result['ap_name'] == 'living-AP1815M'
        assert result['client_state'] == 'Associated'
        assert result['connected_for'] == '44587'
        assert result['device_type'] == 'iPad 6th Gen'
        assert result['gateway_address'] == '192.168.122.1'
        assert result['ip_address'] == '192.168.122.111'
        assert result['mac_address'] == '2e:14:db:b8:9b:d8'
        assert result['netmask'] == '255.255.255.0'
        assert result['username'] == 'N/A'
        assert result['wireless_lan_network_name'] == 'taka 11ac'
        print('test_parse_wlc_show_client_detail() passed')

    def test():
        test_parse_wlc_show_client_summary()
        test_parse_wlc_show_client_detail()
        return 0

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-r', '--run', action='store_true')
    args, _ = parser.parse_known_args()

    def main():

        if args.test:
            return test()

        if args.run:
            # pyATSのテストベッドからwlcに関する情報を取得
            testbed = get_testbed_from_file(testbed_filename='home.yaml')
            inventory = get_inventory(testbed=testbed, device_name='wlc')
            ip = inventory['ip']
            username = inventory['username']
            password = inventory['password']

            wlc = CiscoWlcHandler(ip, username, password)
            with wlc:
                clients_list = wlc.get_wlc_clients()
            pprint(clients_list)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
