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
        'ap_mac_address': re.compile(r'AP\s+MAC\s+Address(\s*)(\.)+\s+(?P<ap_mac_address>(?:[0-9a-fA-F]{2}\:){5}[0-9a-fA-F]{2})(\s*)$', re.MULTILINE),

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


def create_connection_handler(ip, username, password):

    args = {
        'ip': ip,
        'port': 22,
        'username': username,
        'password': password,
        'device_type': 'cisco_wlc_ssh',
        #
        # pass to paramiko
        #
        'conn_timeout': 10,  # default 10
        'banner_timeout': 15,  # default 15
    }

    try:
        return ConnectHandler(**args)
    except NetmikoAuthenticationException as e:
        logger.error('authentication failed.')
        raise e


def get_wlc_clients(ip:str, username:str, password:str):

    # 接続
    try:
        ch = create_connection_handler(ip, username, password)
    except NetmikoAuthenticationException:
        return 0

    results = []

    with ch:
        # show client summaryを叩いてクライアントのMACアドレス情報を取得
        cmd_show_client_summary = 'show client summary'
        output = ch.send_command(cmd_show_client_summary)

        # 出力をパースしてクライアントリストを作成
        client_list = parse_wlc_show_client_summary(output)

        # MACアドレスを取り出して show client detail xx:xx:xx:xx:xx:xx コマンドを実行する
        for client in client_list:
            mac_address = client['mac_address']
            cmd_show_client_detail = f'show client detail {mac_address}'

            output = ch.send_command(cmd_show_client_detail)
            print(output)
            print('')

            # パース
            d = parse_wlc_show_client_detail(output)
            results.append(d)

    return results



if __name__ == '__main__':

    import argparse
    import os
    import sys

    from pprint import pprint

    #
    # libディレクトリをパスに加える
    #
    app_dir = os.path.join(os.path.dirname(__file__), '../..')
    lib_dir = os.path.join(app_dir, 'lib')

    if lib_dir not in sys.path:
        sys.path.append(lib_dir)

    from pyats_util import get_inventory

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('--testbed',
                        dest='testbed',
                        help='testbed YAML file',
                        type=str,
                        default='home.yaml')
    parser.add_argument('--device',
                        dest='device',
                        help='name of the device to connect',
                        type=str,
                        default='wlc')
    args, _ = parser.parse_known_args()


    def test_parse_wlc_show_client_summary():
        path = os.path.join(os.path.dirname(__file__), 'show_client_summary.txt')
        with open(path) as f:
            cmd_output = f.read()

        client_list = parse_wlc_show_client_summary(cmd_output)
        # pprint(client_list)

        assert {'ap_name': 'living-AP1815M', 'mac_address': '04:03:d6:d8:57:5f', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '08:97:98:04:22:e4', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '20:df:b9:b4:bc:79', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '26:67:ca:be:bc:c9', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'ayane-CAP702I', 'mac_address': '2e:14:db:b8:9b:d8', 'protocol': '802.11n(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '38:1a:52:5b:42:15', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '3c:22:fb:7b:85:0e', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '44:65:0d:da:2a:f5', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '90:9a:4a:d6:bb:b9', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'a0:c9:a0:9a:7f:01', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': 'a4:5e:60:e4:1a:dd', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': 'c6:78:ad:69:2d:fd', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'ayane-CAP702I', 'mac_address': 'ee:e7:80:e3:c3:b2', 'protocol': '802.11n(5 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'f6:ff:cc:5f:51:68', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'fe:dd:b8:3f:de:59', 'protocol': '802.11ac(5 GHz)'} in client_list
        print('test_parse_wlc_show_client_summary() passed')


    def test_parse_wlc_show_client_detail():
        path = os.path.join(os.path.dirname(__file__), 'show_client_detail.txt')
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

    def run_schedule():
        pass


    def main():

        if args.test:
            test()
            return 0

        inventory = get_inventory(testbed_filename=args.testbed, device_name=args.device)

        clients_list = get_wlc_clients(inventory['ip'], inventory['username'], inventory['password'])
        pprint(clients_list)
        return 0

    sys.exit(main())
