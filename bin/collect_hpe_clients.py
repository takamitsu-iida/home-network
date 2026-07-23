#!/usr/bin/env python

#
# Aruba Instant APからクライアント情報を取得します
#

# ap01-aruba-515# show clients
#
# Client List
# -----------
# Name                      IP Address       MAC Address        OS       ESSID      Access Point    Channel  Type  Role       IPv6 Address                            Signal    Speed (mbps)
# ----                      ----------       -----------        --       -----      ------------    -------  ----  ----       ------------                            ------    ------------
# VL-MWH705                 192.168.122.123  b8:20:8e:1b:78:e8  NOFP     taka 11ng  ap02-aruba-515  11       GN    taka 11ng  fe80::ba20:8eff:fe1b:78e8               44(good)  57(good)
#                           192.168.122.106  3a:f1:69:4e:52:69  NOFP     taka 11ng  ap03-aruba-505  11       GN    taka 11ng  2400:2411:561:5b00:c085:acf5:c856:a55f  40(good)  130(good)
# Mac                       192.168.122.109  fa:36:5d:82:7e:f3  NOFP     taka 11ac  ap01-aruba-515  36E      a-HE  taka 11ac  2400:2411:561:5b00:c9b9:9364:adb5:e646  51(good)  720(good)
# iPhone                    192.168.122.107  5e:92:07:07:55:fe  NOFP     taka 11ng  ap03-aruba-505  11       g-HE  taka 11ng  2400:2411:561:5b00:8dd:7c29:ec2e:a19c   51(good)  206(good)
#                           192.168.122.101  c8:48:05:eb:2a:12  NOFP     taka 11ng  ap02-aruba-515  11       g-HE  taka 11ng  2400:2411:561:5b00:72c7:12eb:c14a:7760  50(good)  135(good)
# iPad                      192.168.122.104  ea:7c:f3:d9:b6:62  NOFP     taka 11ac  ap03-aruba-505  116E     a-HE  taka 11ac  2400:2411:561:5b00:b492:1628:943d:7cd3  52(good)  1134(good)
# MAYO-HP                   192.168.122.120  08:9d:f4:25:b0:ed  Win 10   taka 11ac  ap02-aruba-515  100E     a-HE  taka 11ac  2400:2411:561:5b00:c0ff:a7cf:8c:f0eb    39(good)  1134(good)
# Ayane-PC                  192.168.122.116  00:a5:54:c5:67:19  Win 11   taka 11ng  ap02-aruba-515  11       g-HE  taka 11ng  2400:2411:561:5b00:3c75:719:df27:4f11   47(good)  243(good)
# C100                      192.168.122.162  98:25:4a:82:25:c7  NOFP     taka 11ng  ap02-aruba-515  11       GN    taka 11ng  --                                      63(good)  65(good)
# iidataknoiPhone           192.168.122.118  4c:cd:b6:18:72:7e  NOFP     taka 11ac  ap01-aruba-515  36E      a-HE  taka 11ac  2400:2411:561:5b00:9418:13de:3f2f:be7   46(good)  1200(good)
# Google-Home-Mini          192.168.122.102  20:df:b9:b4:bc:79  Android  taka 11ac  ap01-aruba-515  36E      AC    taka 11ac  2400:2411:561:5b00:aca0:1dbe:4353:2ff0  53(good)  292(good)
#                           192.168.122.103  8e:ae:72:98:d1:58  NOFP     taka 11ng  ap03-aruba-505  11       g-HE  taka 11ng  2400:2411:561:5b00:6053:d36d:5edb:a748  60(good)  229(good)
#                           192.168.122.105  38:1a:52:5b:42:15  NOFP     taka 11ng  ap03-aruba-505  11       GN    taka 11ng  fe80::3a1a:52ff:fe5b:4215               29(good)  28(ok)
#                           192.168.122.108  a6:51:b6:4c:a4:85  NOFP     taka 11ac  ap03-aruba-505  116E     AC    taka 11ac  2400:2411:561:5b00:cd26:21f4:2119:80dd  46(good)  780(good)
# Pixel-9a                  192.168.122.113  4e:ee:f9:d8:04:a7  NOFP     taka 11ac  ap03-aruba-505  116E     a-HE  taka 11ac  2400:2411:561:5b00:f583:d58a:9956:9c22  28(good)  510(good)
# amazon-a281150c3          192.168.122.146  44:65:0d:da:2a:f5  NOFP     taka 11ng  ap02-aruba-515  11       GN    taka 11ng  2400:2411:561:5b00:f4dd:5c5c:ba2d:9c4f  65(good)  130(good)
#                           192.168.122.110  f6:ff:cc:5f:51:68  Android  taka 11ac  ap01-aruba-515  36E      AC    taka 11ac  2400:2411:561:5b00:d0c0:3b1a:658f:7d9c  50(good)  433(good)
# iPhone                    192.168.122.114  ee:b7:4c:04:ef:cd  NOFP     taka 11ac  ap03-aruba-505  116E     a-HE  taka 11ac  2400:2411:561:5b00:e962:3a25:914c:485c  35(good)  540(good)
# Toshiba_ac_A134           192.168.122.148  44:35:d3:66:a1:34  NOFP     taka 11ng  ap03-aruba-505  11       G     taka 11ng  --                                      25(good)  18(ok)
#                           192.168.122.115  56:3a:39:80:1b:4f  NOFP     taka 11ac  ap02-aruba-515  100E     a-HE  taka 11ac  2400:2411:561:5b00:d9c4:4818:178d:21e   47(good)  1134(good)
# android_f9caac6b1bedab65  192.168.122.124  b0:ee:45:68:d0:e9  Android  taka 11ng  ap02-aruba-515  11       GN    taka 11ng  2400:2411:561:5b00:b2ee:45ff:fe68:d0e9  44(good)  65(good)
# Number of Clients   :21
# Info timestamp      :764276
#


import argparse
import json
import logging
import os
import re
import sys

logger = logging.getLogger(__name__)

try:
    from genie.testbed import load
except ImportError as e:
    logger.error(f"Error importing genie.testbed: {e}")
    sys.exit(1)

#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/pyats_util/pyats_util.py
from pyats_util import get_testbed_devices


def get_iap_show_clients_output(testbed_filename: str, device_name: str = 'iap', log_stdout: bool = False) -> str:
    """pyATS で IAP に接続し、`show clients` を実行して出力を得る。"""

    # テストベッドのデバイス一覧を取得
    devices = get_testbed_devices(testbed_filename)
    if not devices:
        return None

    dev = devices.get(device_name, None)
    if not dev:
        return None

    try:
        dev.connect(log_stdout=log_stdout, logfile=os.devnull, no_pyats_tasklog=True)
        output = dev.execute('show clients')
    finally:
        if dev.is_connected():
            dev.disconnect()

    return output



def parse_iap_show_clients(output: str) -> dict:
    """
    Aruba Instant AP の `show clients` 出力をパースして辞書化する。

    Returns:
        {
            'clients': [
                {
                    'name': ..., 'ip_address': ..., 'mac_address': ...,
                    'os': ..., 'essid': ..., 'access_point': ..., 'channel': ...,
                    'type': ..., 'role': ..., 'ipv6_address': ..., 'signal': ..., 'speed_mbps': ...
                },
                ...
            ],
            'number_of_clients': int,
            'info_timestamp': int | None,
        }
    """

    result = {
        'clients': [],
        'number_of_clients': 0,
        'info_timestamp': None,
    }

    ip_regexp = re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}$')
    in_client_section = False

    for line in output.splitlines():
        line = line.rstrip()

        if line.startswith('Client List'):
            in_client_section = True
            continue

        if not in_client_section:
            continue

        if line.startswith('Number of Clients'):
            try:
                result['number_of_clients'] = int(line.split(':', 1)[1].strip())
            except ValueError:
                result['number_of_clients'] = 0
            continue

        if line.startswith('Info timestamp'):
            try:
                result['info_timestamp'] = int(line.split(':', 1)[1].strip())
            except ValueError:
                result['info_timestamp'] = None
            continue

        if line.startswith('Name') or line.startswith('----') or not line.strip():
            continue

        parts = [p for p in re.split(r'\s{2,}', line.strip()) if p]
        if not parts:
            continue

        # 名前欄が空の行は、列順が IP Address から始まるので、name を補填する
        if ip_regexp.match(parts[0]):
            columns = parts
            name = ''
        elif len(parts) >= 12:
            name = parts[0]
            columns = parts[1:]
        else:
            continue

        if len(columns) < 11:
            continue

        client = {
            'name': name,
            'ip_address': columns[0],
            'mac_address': columns[1],
            'os': columns[2],
            'essid': columns[3],
            'access_point': columns[4],
            'channel': columns[5],
            'type': columns[6],
            'role': columns[7],
            'ipv6_address': columns[8],
            'signal': columns[9],
            'speed_mbps': columns[10],
        }

        result['clients'].append(client)

    return result



if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='show iap clients')
    parser.add_argument('-s', '--silent', action='store_true', default=False, help='supress device log to stdout')
    parser.add_argument('-g', '--get', action='store_true', default=False, help='get iap clients info')
    args = parser.parse_args()

    def main():

        logger.addHandler(logging.NullHandler())

        if args.get:
            # pyATSの接続状況を画面表示するかどうか
            log_stdout = True if args.silent is False else False

            output = get_iap_show_clients_output(testbed_filename='home.yaml', log_stdout=log_stdout)
            if output is None or not output.strip():
                logger.error('Failed to get show clients output from IAP.')
                return 1

            if log_stdout:
                print('show clients output:')
                print(output)
                print()

            result = parse_iap_show_clients(output)
            json.dump(result, sys.stdout, indent=4, ensure_ascii=False)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
