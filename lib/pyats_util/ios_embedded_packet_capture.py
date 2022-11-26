#!/usr/bin/env python

import logging
import os
import re

#
# import pyATS module
#
from genie.testbed import load
from unicon.core.errors import TimeoutError, StateMachineError, ConnectionError
from unicon.core.errors import SubCommandFailure

logger = logging.getLogger(__name__)


class IosEmbeddedPacketCapture:

    def __init__(self, buffer_name: str, point_name: str, capture_target: str = 'process-switched') -> None:
        self.buffer_name = buffer_name
        self.point_name = point_name

        self.capture_target = capture_target
        # これが'process-switched'の場合はこう
        # monitor capture point ip process-switched <point_name> both

        # それ以外はキャプチャするインタフェースと判断する
        # monitor capture point ip cef <point_name> <capture_target> both

        # parameters
        self.buffer_type = 'linear'  #  Linear Buffer(Default) or 'circular'
        self.buffer_size = 1024  # <256-102400>  Buffer size in Kbytes : 102400K or less (default is 1024K)
        self.max_size = 68  # <68-9500>  Element size in bytes : 9500 bytes or less (default is 68 bytes)
        self.filter_name = None  # monitor capture buffer BUF filter access-list <name>


    def build_config(self):
        lines = []

        cmd = f'monitor capture buffer {self.buffer_name} size {self.buffer_size} max-size {self.max_size} {self.buffer_type}'
        lines.append(cmd)

        if self.filter_name:
            cmd = f'monitor capture buffer {self.buffer_name} filter access-list {self.filter_name}'
            lines.append(cmd)

        if self.capture_target == 'process-switched':
            cmd = f'monitor capture point ip process-switched {self.point_name} both'
            lines.append(cmd)
        else:
            cmd = f'monitor capture point ip cef {self.point_name} {self.capture_target} both'
            lines.append(cmd)

        cmd = f'monitor capture point associate {self.point_name} {self.buffer_name}'
        lines.append(cmd)

        return lines


    def apply_config(self, device: object, disconnect_on_finished=False):
        if not device.is_connected():
            try:
                device.connect()
            except (TimeoutError, StateMachineError, ConnectionError) as e:
                logger.error(str(e))
                return

        status = self.retrieve_monitor_status(device=device, disconnect_on_finished=False)
        existing_lines = status.get('configurations', [])

        lines = self.build_config()
        for line in lines:
            if line in existing_lines:
                logger.info(f'skipped already configured: {line}')
                continue
            output = device.execute(line)
            logger.info(output)

        if disconnect_on_finished and device.is_connected():
            device.disconnect()


    def build_unconfig(self):
        lines = []
        cmd = f'no monitor capture buffer {self.buffer_name}'
        lines.append(cmd)

        if self.capture_target == 'process-switched':
            cmd = f'no monitor capture point ip process-switched {self.point_name}'
            lines.append(cmd)
        else:
            cmd = f'no monitor capture point ip cef {self.point_name} {self.capture_target}'
            lines.append(cmd)

        return lines


    def apply_unconfig(self, device: object, disconnect_on_finished=False):
        if not device.is_connected():
            try:
                device.connect()
            except (TimeoutError, StateMachineError, ConnectionError) as e:
                logger.error(str(e))
                return

        status = self.retrieve_monitor_status(device=device, disconnect_on_finished=False)
        configurations = status.get('configurations', [])
        if status.get('status') == 'Active':
            logger.info('skipped, packet capture is running')
        elif len(configurations) == 0:
            logger.info('skipped, not configured')
        else:
            lines = self.build_unconfig()
            for line in lines:
                output = device.execute(line)
                logger.info(output)

        if disconnect_on_finished and device.is_connected():
            device.disconnect()



    def start_capture(self, device: object, disconnect_on_finished=False):
        if not device.is_connected():
            try:
                device.connect()
            except (TimeoutError, StateMachineError, ConnectionError) as e:
                logger.error(str(e))
                return

        status = self.retrieve_monitor_status(device=device, disconnect_on_finished=False)
        if status.get('status') == 'Active':
            logger.info('skipped already running')
        elif status.get('associated_point') is None:
            logger.info('skipped not configured association')
        else:
            command = f'monitor capture point start {self.point_name}'
            try:
                device.execute(command)
            except SubCommandFailure as e:
                raise SubCommandFailure(f'Failed in monitor capture, Error: {str(e)}') from e

        if disconnect_on_finished and device.is_connected():
            device.disconnect()


    def stop_capture(self, device: object,  disconnect_on_finished=False):
        if not device.is_connected():
            try:
                device.connect()
            except (TimeoutError, StateMachineError, ConnectionError) as e:
                logger.error(str(e))
                return

        status = self.retrieve_monitor_status(device=device, disconnect_on_finished=False)
        if status.get('status') == 'Inactive':
            logger.info('skipped not running')
        else:
            command = f'monitor capture point stop {self.point_name}'
            try:
                device.execute(command)
            except SubCommandFailure as e:
                raise SubCommandFailure(
                    f'Failed in monitor capture, Error: {str(e)}') from e

        if disconnect_on_finished and device.is_connected():
            device.disconnect()


    def export_to_flash(self, device: object):
        pass


    def retrieve_monitor_status(self, device: object, disconnect_on_finished=False) -> dict:
        if not device.is_connected():
            try:
                device.connect()
            except (TimeoutError, StateMachineError, ConnectionError) as e:
                logger.error(str(e))
                return

        status = {}

        command = f'show monitor capture point {self.point_name}'

        try:
            output = device.execute(command)
        except SubCommandFailure as e:
            raise SubCommandFailure(
                f'Failed in monitor capture, Error: {str(e)}') from e

        parsed_point = self.parse_show_monitor_capture_point(output)

        command = f'show monitor capture buffer {self.buffer_name} parameters'

        try:
            output = device.execute(command)
        except SubCommandFailure as e:
            raise SubCommandFailure(
                f'Failed in monitor capture, Error: {str(e)}') from e

        parsed_buffer = self.parse_show_monitor_capture_buffer(output)

        status['status'] = parsed_point.get('status')
        status['buffer'] = parsed_point.get('buffer')
        status['associated_point'] = parsed_buffer.get('associated_point')
        status['configurations'] = parsed_point.get('configurations', []) + parsed_buffer.get('configurations', [])

        if disconnect_on_finished and device.is_connected():
            device.disconnect()

        return status



    def parse_show_monitor_capture_buffer(self, output: str) -> dict:
        """
        show monitor capture buffer <NAME> parameters 出力をパースして設定済みmonitorコマンドを抽出する

        Args:
            output (str): show monitor capture buffer <NAME> parameters コマンド出力

        result = {
            'status': status,  # None or 'Active' or 'Inactive'
            'associated_point': associated_point,  # None or 'name_of_capture_point'
            'configurations': configuration_list  # []
        }
        """
        '''
        # キャプチャバッファ作成前
        c2960cx-8pc#show monitor capture buffer BUF parameters
        Capture Buffer BUF does not exist

        # キャプチャバッファ作成後
        c2960cx-8pc#show monitor capture buffer BUF parameters
        Capture buffer BUF (circular buffer)
        Buffer Size : 2097152 bytes, Max Element Size : 1518 bytes, Packets : 6
        Allow-nth-pak : 0, Duration : 0 (seconds), Max packets : 0, pps : 0
        Associated Capture Points:
        Name : POINT, Status : Inactive
        Configuration:
        monitor capture buffer BUF size 2048 max-size 1518 circular
        monitor capture point associate POINT BUF
        monitor capture buffer BUF filter access-list CAPTURE-FILTER
        c2960cx-8pc#

        # Configuration:となっている部分に既存の設定が入っているので、その行を取り出して返却する
        '''

        # 行に分解する前にこの部分をマルチラインモードで取り出す
        # Associated Capture Points:
        # Name : POINT, Status : Inactive
        re_associated = re.compile(r'Name : (?P<point>\S+), Status : (?P<status>\S+)', re.MULTILINE)

        match = re_associated.search(output)  # 行頭からの検索ではないのでsearch()を使用
        if match:
            associated_point = match.group('point')
            status = match.group('status')
        else:
            associated_point = None
            status = None

        # 行に分解してConfiguration部分を取り出す
        re_marker = re.compile(r'Configuration')
        re_monitor = re.compile(r'monitor capture [buffer|point]')

        # 結果を格納するリスト
        configuration_list = []

        # 処理中かどうか
        is_section = False

        # 行に分解して走査
        for line in output.splitlines():

            # マーカー行を見つけるまで無用な情報をスキップする
            if not is_section:
                # この行が区切りかどうかを判定
                match = re_marker.match(line)  # 行頭が一致するかどうかを見ればよいのでmatch()を使用
                if match:
                    # マーカーを見つけた
                    is_section = True
                # 次の行に移動
                continue

            # monitorコマンドを取り出す
            match = re_monitor.match(line)

            if match:
                configuration_list.append(line.strip())
                # この行は取り込んだので次の行へ
                continue

            break

        result = {
            'status': status,  # None or Inactive or Active
            'associated_point': associated_point,
            'configurations': configuration_list
        }

        return result


    def parse_show_monitor_capture_point(self, output: str) -> dict:
        """
        show monitor capture point POINT コマンドを出力をパースする

        Args:
            output (str): _description_

        Returns:
            dict: _description_

            # 返却する辞書型
            {
                'status': Inactive or Active,
                'buffer': None or name
                'configurations': [
                    'monitor capture point ip process-switched POINT both
                ]
            }
        """
        '''
        # キャプチャポイントが存在しない場合
        c2960cx-8pc#show monitor capture point POINT
        Capture point POINT does not exist

        # キャプチャポイントを作成したが、バッファとの関連付けがない場合
        c2960cx-8pc#show monitor capture point POINT
        Status Information for Capture Point POINT
        IPv4 Process
        Switch Path: IPv4 Process        , Capture Buffer: None
        Status : Inactive

        Configuration:
        monitor capture point ip process-switched POINT both

        # キャプチャ前
        Status Information for Capture Point POINT
        IPv4 Process
        Switch Path: IPv4 Process        , Capture Buffer: BUF
        Status : Inactive

        Configuration:
        monitor capture point ip process-switched POINT both

        # キャプチャ実行中
        c2960cx-8pc#show monitor capture point POINT
        Status Information for Capture Point POINT
        IPv4 Process
        Switch Path: IPv4 Process        , Capture Buffer: BUF
        Status : Active

        Configuration:
        monitor capture point ip process-switched POINT both
        '''

        re_marker = re.compile(r'Configuration')
        re_monitor = re.compile(r'monitor capture point')
        re_buffer = re.compile(r'Switch Path.*Capture Buffer\:\s*(?P<buffer>\S+)')
        re_status = re.compile(r'Status : (?P<status>\S+)')

        # 戻り値の辞書型
        d = {'status': None, 'buffer': None, 'configurations': []}

        # 処理中かどうか
        is_section = False

        # 行に分解して走査
        for line in output.splitlines():

            # print(line)

            match = re_buffer.match(line)  # 行頭が一致するかどうかを見ればよいのでmatch()を使用
            if match:
                d['buffer'] = match.group('buffer')
                continue

            match = re_status.match(line)
            if match:
                d['status'] = match.group('status')
                continue

            # マーカー行を見つけるまで無用な情報をスキップする
            if not is_section:
                # この行が区切りかどうかを判定
                match = re_marker.match(line)
                if match:
                    # マーカーを見つけた
                    is_section = True
                # 次の行に移動
                continue

            #
            match = re_monitor.match(line)  # 行頭が一致するかどうかを見ればよいのでmatch()を使用
            if match:
                d['configurations'].append(line)
                # この行は取り込んだので次の行へ
                continue

            break

        return d









if __name__ == '__main__':

    import argparse
    import sys
    from pprint import pprint

    logging.basicConfig(level=logging.INFO)

    # yapf: disable
    parser = argparse.ArgumentParser(description='test for ios_embedded_packet_capture.py')
    parser.add_argument('-t', '--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    parser.add_argument('-d', '--device', dest='device', help='device name', type=str, default='uut')
    parser.add_argument('-bc', '--build_config', action='store_true', default=False, help='build config')
    parser.add_argument('-bu', '--build_unconfig', action='store_true', default=False, help='build unconfig')
    parser.add_argument('-ac', '--apply_config', action='store_true', default=False, help='apply config')
    parser.add_argument('-au', '--apply_unconfig', action='store_true', default=False, help='apply unconfig')
    parser.add_argument('--start', action='store_true', default=False, help='start monitor')
    parser.add_argument('--stop', action='store_true', default=False, help='start monitor')
    parser.add_argument('-s', '--status', action='store_true', default=False, help='retrieve monitor status')

    args = parser.parse_args()
    # yapf: enable


    def main():

        try:
            testbed_path = os.path.join(os.path.dirname(__file__), args.testbed)
            testbed = load(testbed_path)
            uut = testbed.devices[args.device]
        except:
            return -1

        epc = IosEmbeddedPacketCapture('BUF', 'POINT')
        epc.buffer_size = 2048
        epc.max_size = 1518
        epc.filter_name = 'CAPTURE-FILTER'

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


        if args.status:
            status = epc.retrieve_monitor_status(device=uut)
            print('='*10)
            pprint(status)
            print('='*10)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
