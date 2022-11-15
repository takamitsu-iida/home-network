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


def filter_func(key: str = '', query: str = '') -> callable:
    """
    辞書型を検索する関数を返却する（単一階層のみ）

    想定する使い方
    results配列に格納されているdictのうち、output_dropsキーが0のものだけを抽出する

    f = filter_func(key='output drops', value_query='[^0]')
    filtered = [d for d in results if f(d)]

    Arguments:
      key {str} -- 対象のキー
      query {str} -- 対象のキーに対応する値を検索する正規表現文字列

    Returns:
      function -- 辞書型オブジェクトを引数にとり、一致した場合にそれを返却する
    """
    if not key:
        return None

    r = re.compile(r'%s' % query, re.IGNORECASE)

    # この関数を返却する
    # 深い階層まで探索したければこれを改造
    def _filter(d):
        ret = None
        v = d.get(key, '')
        if r.search(v):
            ret = d
        return ret

    return _filter


def and_filter(d: dict, funcs: list) -> dict:
    """
    オブジェクトとフィルタ関数の配列を受け取り、and条件で検索する

    想定する使い方
    results配列に格納されているdictのうち、output_dropsキーが0 かつ duplexキーがfullのものだけを抽出する

    f1 = filter_func(key='output drops', value_query='[^0]')
    f2 = filter_func(key='duplex', value_query='full')
    filtered = [d for d in results if and_filter(d, [f1, f2])]

    Arguments:
        d {dict} -- 検索対象のdict
        funcs {list} -- フィルタ関数のリスト

    Returns:
        d -- フィルタ関数をすべて適用して残ったオブジェクト、一致しない場合はNoneを返す
    """
    func = funcs[0]
    result = func(d)
    if result and funcs[1:]:
        return filter(d, funcs[1:])

    return result

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
    parser.add_argument('--testbed',
                        dest='testbed',
                        help='testbed YAML file',
                        type=str,
                        default='home.yaml')
    args, _ = parser.parse_known_args()

    logger.info(f'testbed file: args.testbed')

    def test_parse_wlc_show_client_summary():

        cmd_output = '''
        Number of Clients................................ 16

        Number of EoGRE Clients.......................... 0

                                                                        RLAN/
        MAC Address       AP Name                        Slot Status        WLAN  Auth Protocol         Port Wired Tunnel  Role
        ----------------- ------------------------------ ---- ------------- ----- ---- ---------------- ---- ----- ------- ----------------
        04:03:d6:d8:57:5f living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        08:97:98:04:22:e4 living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        20:df:b9:b4:bc:79 taka-AP1815I                    1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
        26:67:ca:be:bc:c9 living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        2e:14:db:b8:9b:d8 living-AP1815M                  1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
        38:1a:52:5b:42:15 living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        3c:22:fb:7b:85:0e taka-AP1815I                    1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
        44:65:0d:da:2a:f5 living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        84:5c:f3:48:ff:30 taka-AP1815I                    0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        90:9a:4a:d6:bb:b9 taka-AP1815I                    0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        a0:c9:a0:9a:7f:01 taka-AP1815I                    1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
        a4:5e:60:e4:1a:dd living-AP1815M                  1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
        c6:78:ad:69:2d:fd living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
        ee:e7:80:e3:c3:b2 ayane-CAP702I                   1   Associated     1    Yes   802.11n(5 GHz)   1    N/A   No      Local
        f6:ff:cc:5f:51:68 taka-AP1815I                    1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
        fe:dd:b8:3f:de:59 taka-AP1815I                    1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
        '''

        client_list = parse_wlc_show_client_summary(cmd_output)
        # pprint(client_list)

        assert {'ap_name': 'living-AP1815M', 'mac_address': '04:03:d6:d8:57:5f', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '08:97:98:04:22:e4', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '20:df:b9:b4:bc:79', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '26:67:ca:be:bc:c9', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '2e:14:db:b8:9b:d8', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '38:1a:52:5b:42:15', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '3c:22:fb:7b:85:0e', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': '44:65:0d:da:2a:f5', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '84:5c:f3:48:ff:30', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': '90:9a:4a:d6:bb:b9', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'a0:c9:a0:9a:7f:01', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': 'a4:5e:60:e4:1a:dd', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'living-AP1815M', 'mac_address': 'c6:78:ad:69:2d:fd', 'protocol': '802.11n(2.4 GHz)'} in client_list
        assert {'ap_name': 'ayane-CAP702I', 'mac_address': 'ee:e7:80:e3:c3:b2', 'protocol': '802.11n(5 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'f6:ff:cc:5f:51:68', 'protocol': '802.11ac(5 GHz)'} in client_list
        assert {'ap_name': 'taka-AP1815I', 'mac_address': 'fe:dd:b8:3f:de:59', 'protocol': '802.11ac(5 GHz)'} in client_list
        print('test_parse_wlc_show_client_summary() passed')



    def test_parse_wlc_show_client_detail():
        cmd_output = '''
        Client MAC Address............................... 04:03:d6:d8:57:5f
        Client Username ................................. N/A
        Client Webauth Username ......................... N/A
        Hostname: .......................................
        Device Type: .................................... NintendoWII
        AP MAC Address................................... 70:ea:1a:84:16:c0
        AP Name.......................................... living-AP1815M
        AP radio slot Id................................. 0
        Client State..................................... Associated
        User Authenticated by ........................... None
        Client User Group................................
        Client NAC OOB State............................. Access
        Wireless LAN Id.................................. 2
        Wireless LAN Network Name (SSID)................. taka 11ng
        Wireless LAN Profile Name........................ taka 11ng
        WLAN Profile check for roaming................... Disabled
        Hotspot (802.11u)................................ Not Supported
        Connected For ................................... 4946 secs
        BSSID............................................ 70:ea:1a:84:16:c1
        Channel.......................................... 6
        IP Address....................................... 192.168.122.107
        Gateway Address.................................. 192.168.122.1
        Netmask.......................................... 255.255.255.0
        Association Id................................... 3
        Authentication Algorithm......................... Open System
        Reason Code...................................... 1
        Client IPSK-TAG.................................. N/A
        Status Code...................................... 0
        Session Timeout.................................. 0
        Client CCX version............................... No CCX support
        QoS Level........................................ Silver
        Avg data Rate.................................... 0
        Burst data Rate.................................. 0
        Avg Real time data Rate.......................... 0
        Burst Real Time data Rate........................ 0
        Avg Uplink data Rate............................. 0
        Burst Uplink data Rate........................... 0
        Avg Uplink Real time data Rate................... 0
        Burst Uplink Real Time data Rate................. 0
        802.1P Priority Tag.............................. disabled
        Security Group Tag............................... Unknown(0)
        KTS CAC Capability............................... No
        Qos Map Capability............................... No
        WMM Support...................................... Enabled
        APSD ACs.......................................  BK  BE  VI  VO
        Current Rate..................................... m7 ss1
        Supported Rates.................................. 11.0,6.0,9.0,12.0,18.0,24.0,
            ............................................. 36.0,48.0,54.0
        Mobility State................................... Local
        Mobility Move Count.............................. 0
        Security Policy Completed........................ Yes
        Policy Manager State............................. RUN
        Pre-auth IPv4 ACL Name........................... none
        Pre-auth IPv4 ACL Applied Status................. Unavailable
        Pre-auth IPv6 ACL Name........................... none
        Pre-auth IPv6 ACL Applied Status................. Unavailable
        Pre-auth Flex IPv4 ACL Name...................... none
        Pre-auth Flex IPv4 ACL Applied Status............ Unavailable
        Pre-auth Flex IPv6 ACL Name...................... none
        Pre-auth Flex IPv6 ACL Applied Status............ Unavailable
        Pre-auth redirect URL............................ none
        Audit Session ID................................. fd7aa8c0000003cd27217363
        AAA Role Type.................................... none
        Acct Interim Interval............................ 0
        Local Policy Applied............................. none
        IPv4 ACL Name.................................... none
        AAA FlexConnect ACL Applied Status............... Unavailable
        IPv4 ACL Applied Status.......................... Unavailable
        IPv6 ACL Name.................................... none
        IPv6 ACL Applied Status.......................... Unavailable
        Post-auth Flex IPv6 ACL Name..................... none
        Post-auth Flex IPv6 ACL Applied Status........... Unavailable
        Layer2 ACL Name.................................. none
        Layer2 ACL Applied Status........................ Unavailable
        mDNS Status...................................... Disabled
        mDNS Profile Name................................ none
        No. of mDNS Services Advertised.................. 0
        Policy Type...................................... WPA2
        Authentication Key Management.................... PSK
        Encryption Cipher................................ CCMP-128 (AES)
        Protected Management Frame ...................... No
        Management Frame Protection...................... No
        EAP Type......................................... Unknown
        FlexConnect Data Switching....................... Local
        FlexConnect Dhcp Status.......................... Local
        FlexConnect Vlan Based Central Switching......... No
        FlexConnect Authentication....................... Central
        FlexConnect Central Association.................. No
        FlexConnect VLAN NAME............................ Unavailable
        Quarantine VLAN.................................. 0
        Access VLAN...................................... 0
        Local Bridging VLAN.............................. 0
        Client Capabilities:
            Radio Capability........................... 802.11n
            CF Pollable................................ Not implemented
            CF Poll Request............................ Not implemented
            Short Preamble............................. Implemented
            PBCC....................................... Not implemented
            Channel Agility............................ Not implemented
            Listen Interval............................ 10
            Fast BSS Transition........................ Not implemented
            11v BSS Transition......................... Not implemented
        Non-Operable Channels............................ None
        Non-Prefer Channels.............................. None
        Client Wifi Direct Capabilities:
            WFD capable................................ No
            Manged WFD capable......................... No
            Cross Connection Capable................... No
            Support Concurrent Operation............... No
        Fast BSS Transition Details:
        DNS Server details:
            DNS server IP ............................. 192.168.122.1
            DNS server IP ............................. 0.0.0.0
        Assisted Roaming Prediction List details:


        Client Dhcp Required:     False
        Allowed (URL)IP Addresses
        -------------------------

        AVC Profile Name: ............................... none
        OpenDns Profile Name: ........................... none
        Fastlane Client: ................................ No
        Max DSCP: ....................................... 0
        Nas Identifier: ................................. AIR-AP1815M-Q
        Client Statistics:
            Number of Bytes Received................... 55948
            Number of Bytes Sent....................... 90794
            Total Number of Bytes Sent................. 90794
            Total Number of Bytes Recv................. 55948
            Number of Bytes Sent (last 90s)............ 60
            Number of Bytes Recv (last 90s)............ 54
            Number of Packets Received................. 224
            Number of Packets Sent..................... 252
            Number of Interim-Update Sent.............. 0
            Number of EAP Id Request Msg Timeouts...... 0
            Number of EAP Id Request Msg Failures...... 0
            Number of EAP Request Msg Timeouts......... 0
            Number of EAP Request Msg Failures......... 0
            Number of EAP Key Msg Timeouts............. 0
            Number of EAP Key Msg Failures............. 0
            Number of Data Retries..................... 200
            Number of RTS Retries...................... 0
            Number of Duplicate Received Packets....... 0
            Number of Decrypt Failed Packets........... 0
            Number of Mic Failured Packets............. 0
            Number of Mic Missing Packets.............. 0
            Number of RA Packets Dropped............... 0
            Number of Policy Errors.................... 0
            Radio Signal Strength Indicator............ -35 dBm
            Signal to Noise Ratio...................... 53 dB
            Client Detected as Inactive................ No
        Client RBACL Statistics:
            Number of RBACL Allowed Packets............ 0
            Number of RBACL Denied Packets............. 0
        Client Rate Limiting Statistics:
            Number of Data Packets Received............ 0
            Number of Data Rx Packets Dropped.......... 0
            Number of Data Bytes Received.............. 0
            Number of Data Rx Bytes Dropped............ 0
            Number of Realtime Packets Received........ 0
            Number of Realtime Rx Packets Dropped...... 0
            Number of Realtime Bytes Received.......... 0
            Number of Realtime Rx Bytes Dropped........ 0
            Number of Data Packets Sent................ 0
            Number of Data Tx Packets Dropped.......... 0
            Number of Data Bytes Sent.................. 0
            Number of Data Tx Bytes Dropped............ 0
            Number of Realtime Packets Sent............ 0
            Number of Realtime Tx Packets Dropped...... 0
            Number of Realtime Bytes Sent.............. 0
            Number of Realtime Tx Bytes Dropped........ 0
        Nearby AP Statistics:
            living-AP1815M(slot 0)
                antenna0: 4945 secs ago.................. -53 dBm
                antenna1: 4945 secs ago.................. -53 dBm
        '''

        result = parse_wlc_show_client_detail(cmd_output)
        # pprint(result)

        assert result['ap_mac_address'] == '70:ea:1a:84:16:c0'
        assert result['ap_name'] == 'living-AP1815M'
        assert result['client_state'] == 'Associated'
        assert result['connected_for'] == '4946'
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


    def get_wlc_clients():

        # pyATSのテストベッドからインベントリ情報を取得
        inventory = get_inventory(args.testbed, 'wlc')

        # WLCに接続
        try:
            ch = create_connection_handler(inventory['ip'],
                                           inventory['username'],
                                           inventory['password'])
        except NetmikoAuthenticationException:
            return 0

        results = []

        with ch:
            # show client summaryを叩いてクライアントのMACアドレス情報を取得
            cmd_show_client_summary = 'show client summary'
            output = ch.send_command(cmd_show_client_summary)
            client_list = parse_wlc_show_client_summary(output)

            # MACアドレスに関してdetailを取得
            for client in client_list:
                mac_address = client['mac_address']
                cmd_show_client_detail = f'show client detail {mac_address}'

                output = ch.send_command(cmd_show_client_detail)
                print(output)
                print('')
                d = parse_wlc_show_client_detail(output)
                results.append(d)

        # pprint(results)
        return results


    def run_schedule():
        pass



    def main():



        return 0

    # sys.exit(test())
    sys.exit(main())
