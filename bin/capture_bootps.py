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

import logging
import os
import sys




#
# libディレクトリをパスに加える
#
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(app_dir, 'lib')

if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# lib/pyats_util/pyats_util.py
from pyats_util import get_testbed_from_file

logger = logging.getLogger(__name__)







__show_monitor_capture_buffer_output_1 = '''
Capture Buffer BUF does not exist
'''

__show_monitor_capture_buffer_output_2 = '''
Capture buffer BUF (circular buffer)
Buffer Size : 2097152 bytes, Max Element Size : 1518 bytes, Packets : 6
Allow-nth-pak : 0, Duration : 0 (seconds), Max packets : 0, pps : 0
Associated Capture Points:
Name : POINT, Status : Inactive
Configuration:
monitor capture buffer BUF size 2048 max-size 1518 circular
monitor capture point associate POINT BUF
monitor capture buffer BUF filter access-list CAPTURE-FILTER
'''


__show_monitor_capture_point_output_1 = '''
Capture point POINT does not exist
'''

__show_monitor_capture_point_output_2 = '''
c2960cx-8pc#show monitor capture point POINT
Status Information for Capture Point POINT
IPv4 Process
Switch Path: IPv4 Process        , Capture Buffer: None
Status : Inactive

Configuration:
monitor capture point ip process-switched POINT both
'''

__show_monitor_capture_point_output_3 = '''
Status Information for Capture Point POINT
IPv4 Process
Switch Path: IPv4 Process        , Capture Buffer: BUF
Status : Inactive

Configuration:
monitor capture point ip process-switched POINT both
'''

__show_monitor_capture_point_output_4 = '''
Status Information for Capture Point POINT
IPv4 Process
Switch Path: IPv4 Process        , Capture Buffer: BUF
Status : Active

Configuration:
monitor capture point ip process-switched POINT both
'''

if __name__ == '__main__':

    import argparse

    logging.basicConfig(level=logging.INFO)

    # yapf: disable
    parser = argparse.ArgumentParser(description='control embedded packet capture')
    parser.add_argument('-t', '--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    parser.add_argument('-d', '--debug', action='store_true', default=False, help='debug parser func')
    args = parser.parse_args()
    # yapf: enable



    def main():

        if args.debug:
            return 0

        parser.print_help()
        return 0

    sys.exit(main())