#!/usr/bin/env python

#
# 2台のCatalystのコンフィグを互いにフラッシュメモリにコピーしあいます
#

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

# lib/pyats_util/ios_scp.py
from pyats_util import scp_dev_to_dev

logger = logging.getLogger(__name__)



def copy_startup_to_peer(local_device, remote_device):

    # コピー元のファイル
    local_path = 'startup-config'

    # 対向装置にこのファイル名で送り込む
    remote_path = f'{local_device.name}.{local_path}'

    # リモート側装置の名前
    remote_device_name = remote_device.name

    # connect
    local_device.connect()

    # scp startup_config to remote_device
    result = scp_dev_to_dev(local_device=local_device, local_path=local_path, remote_device_name=remote_device_name, remote_path=remote_path)

    # disconnect
    if local_device.is_connected():
        local_device.disconnect()

    return result


if __name__ == '__main__':

    import argparse

    logging.basicConfig(level=logging.INFO)

    # yapf: disable
    parser = argparse.ArgumentParser(description='backup catalyst startup-config')
    parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    parser.add_argument('-r', '--run', action='store_true', default=False, help='run backup startup-config each other')
    args = parser.parse_args()
    # yapf: enable

    def run_backup():

        testbed = get_testbed_from_file(args.testbed)

        catalyst_switches = []
        for device in testbed.devices.values():
            if device.os == 'ios' and device.type == 'switch':
                catalyst_switches.append(device)

        if len(catalyst_switches) < 2:
            logger.error('there must be at least two catalyst switches.')
            return 0

        # 先頭の2台で実行する
        copy_startup_to_peer(catalyst_switches[0], catalyst_switches[1])

        # コピー元と先を入れ替えて実行する
        copy_startup_to_peer(catalyst_switches[1], catalyst_switches[0])

        return 0


    def main():

        if args.run:
            return run_backup()

        parser.print_help()
        return 0

    sys.exit(main())