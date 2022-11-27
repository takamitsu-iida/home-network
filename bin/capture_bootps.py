#!/usr/bin/env python

#
# IOSの基本EPC(Embedded Packet Capture)でbootpsパケットをキャプチャします。
# bootpsパケットはDHCPクライアントが送信するブロードキャストパケットでプロセススイッチで中継されます。
# したがってキャプチャする場所はインタフェースではなくプロセススイッチです。
# DHCPサーバからの戻りパケットはユニキャストで、これはcefスイッチになります。
# bootpsとbootpcの両方を同時にはキャプチャすることはできません。
#
# 参考
# https://www.cisco.com/c/ja_jp/support/docs/ios-nx-os-software/ios-embedded-packet-capture/116045-productconfig-epc-00.html
#

# キャプチャポイント名 POINT
# キャプチャバッファ名 BUF
# キャプチャフィルタ名 CAPTURE-FILTER

# 事前準備： アクセスリストを事前に設定する必要がある
# !
# ip access-list extended CAPTURE-FILTER
#  permit udp any any eq bootps
#  permit udp any any eq bootpc
# !

# バッファの作成
# monitor capture buffer BUF size 2048 max-size 1518 circular

# アクセスリストとの関連付け、アクセスリストは存在しなくてもエラーにはならない（後でアクセスリストを作成してもよい）
# monitor capture buffer BUF2 filter access-list CAPTURE-FILTER

# キャプチャポイントの作成
# monitor capture point ip process-switched POINT both

# キャプチャポイントとバッファの関連付け
# monitor capture point associate POINT BUF


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

# lib/pyats_util/pyats_util.py
from pyats_util import get_testbed_from_file, get_inventory

# lib/pyats_util/ios_embedded_packet_capture.py
from pyats_util import IosEmbeddedPacketCapture

# lib/netmiko_util/transfer.py
from netmiko_util import transfer

# ログディレクトリを（なければ）作成する
log_dir = os.path.join(app_dir, 'log')
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger(__name__)


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    # yapf: disable
    parser = argparse.ArgumentParser(description='control embedded packet capture')
    parser.add_argument('-t', '--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    parser.add_argument('-d', '--device', dest='device', help='device name', type=str, default='c2960cx-8pc')  # デフォルトはc2960cx-8pc
    parser.add_argument('-bc', '--build_config', action='store_true', default=False, help='build config')
    parser.add_argument('-bu', '--build_unconfig', action='store_true', default=False, help='build unconfig')
    parser.add_argument('-ac', '--apply_config', action='store_true', default=False, help='apply config')
    parser.add_argument('-au', '--apply_unconfig', action='store_true', default=False, help='apply unconfig')
    parser.add_argument('--start', action='store_true', default=False, help='start monitor')
    parser.add_argument('--stop', action='store_true', default=False, help='start monitor')
    parser.add_argument('--export', action='store_true', default=False, help='export to flash memory')
    parser.add_argument('--get', action='store_true', default=False, help='get pcap')
    parser.add_argument('--status', action='store_true', default=False, help='retrieve monitor status')
    # yapf: enable

    args = parser.parse_args()

    def main():

        try:
            testbed = get_testbed_from_file(args.testbed)
            uut = testbed.devices[args.device]
            inventory = get_inventory(testbed=testbed, device_name=args.device)
        except:
            return -1

        buffer_name = 'BUF'
        point_name = 'POINT'
        filter_name = 'CAPTURE-FILTER'
        buffer_size = 2048
        max_size = 1518

        epc = IosEmbeddedPacketCapture(buffer_name=buffer_name, point_name=point_name)
        epc.buffer_size = buffer_size
        epc.max_size = max_size
        epc.filter_name = filter_name

        if args.build_config:
            lines = epc.build_config()
            print('\n'.join(lines))
            return 0

        if args.build_unconfig:
            lines = epc.build_unconfig()
            print('\n'.join(lines))
            return 0

        if args.apply_config:
            epc.apply_config(device=uut)
            return 0

        if args.apply_unconfig:
            epc.apply_unconfig(device=uut)
            return 0

        if args.start:
            epc.start_capture(device=uut, disconnect_on_finished=True)
            return 0

        if args.stop:
            epc.stop_capture(device=uut, disconnect_on_finished=True)
            return 0

        if args.export:
            epc.export_to_flash(device=uut)
            return 0

        if args.get:
            device_info = {
                'device_type': 'cisco_ios',
                'host': inventory['ip'],
                'username': inventory['username'],
                'password': inventory['password']
            }
            file_info = {
                'source_file': f'{buffer_name}.pcap',
                'dest_file': f'{log_dir}/{buffer_name}.pcap',
                'file_system': 'flash:',
                'direction': 'get',
                'overwrite_file': True
            }
            result = transfer(device_info=device_info, file_info=file_info)
            pprint(result)
            return 0

        if args.status:
            status = epc.retrieve_monitor_status(device=uut)
            print('='*10)
            pprint(status)
            print('='*10)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())