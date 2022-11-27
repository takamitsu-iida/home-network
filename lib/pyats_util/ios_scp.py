#!/usr/bin/env python

import logging
import os

# import pyATS module
from unicon.core.errors import SubCommandFailure
from unicon.eal.dialogs import Dialog, Statement

# ./pyats_util.py
from pyats_util import get_inventory

logger = logging.getLogger(__name__)


def scp_dev_to_dev(local_device: object,
        local_path: str,
        remote_device_name: str,
        remote_path: str,
        vrf: str = '') -> bool:
    """
    指定のlocal_deviceでcopyコマンドを発行してファイルをscpする

    copy startup-config scp://username:password@192.168.122.252/c3560c-12pc-s.startup-config

    remote_pathの最後が/の場合、途中のディレクトリを事前に作成しておかないとエラーになって失敗する

    Args:
        local_device (object): 操作対象の接続済みローカルデバイス
        local_path (str): 操作対象装置側のパス　例 startup-config
        remote_device_name (str): リモートデバイスの名前、テストベッドで定義されていること
        remote_path (str): リモート側のパス（ファイル名）　例 c3560c-12pc-s.startup-config
        vrf (str, optional): 管理アクセス用のvrf名。Defaults to ''.

    Returns:
        bool: scpに成功すればtrue
    """

    # テストベッドを取り出す
    testbed = local_device.testbed

    # リモート側のデバイスのインベントリを取り出す
    inventory = get_inventory(testbed, remote_device_name)

    # リモート側のIPアドレス、ユーザ名、パスワードを取得できなければ失敗
    if inventory is None:
        logger.error('failed to get remote device inventory')
        return False

    remote_ip = inventory.get('ip')
    remote_username = inventory.get('username')
    remote_password = inventory.get('password')

    # if not remote_path.endswith('/'):
    #     remote_path += '/'

    remote_path = f'scp://{remote_username}:{remote_password}@{remote_ip}/{remote_path}'

    # Address or name of remote host [192.168.122.252]?
    s1 = Statement(pattern=r'.*Address or name of remote host',
                   action='sendline()',
                   args=None,
                   loop_continue=True,
                   continue_timer=False)

    # Destination username [cisco]?
    s2 = Statement(pattern=r'.*Destination username',
                   action='sendline()',
                   args=None,
                   loop_continue=True,
                   continue_timer=False)

    # Destination filename [c3560c-12pc-s.startup-config]?
    s3 = Statement(pattern=r'.*Destination filename',
                   action='sendline()',
                   args=None,
                   loop_continue=True,
                   continue_timer=False)

    dialog = Dialog([s1, s2, s3])

    if vrf:
        cmd = f'copy {local_path} {remote_path} vrf {vrf}'
    else:
        cmd = f'copy {local_path} {remote_path}'

    logger.info(cmd)

    try:
        output = local_device.execute(cmd, reply=dialog)
    except SubCommandFailure as e:
        logger.warning(f'failed to copy from {local_device} {local_path} to {remote_device_name}')
        logger.warning(f'{e}')
        return False
    except Exception as e:
        logger.warning(f'failed to copy from {local_device} {local_path} to {remote_device_name}')
        logger.warning(f'{e}')
        return False

    # Writing c3560c-12pc-s.startup-config !
    # 3483 bytes copied in 1.292 secs (2696 bytes/sec)

    return 'copied in' in output


if __name__ == '__main__':

    import argparse
    import sys
    from pprint import pprint


    from genie.testbed import load

    logging.basicConfig(level=logging.INFO)

    # yapf: disable
    parser = argparse.ArgumentParser(description='test for pyats_util.py')
    parser.add_argument('-t', '--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    parser.add_argument('-r', '--run', action='store_true', default=False, help='test scp with real device')
    args = parser.parse_args()
    # yapf: enable


    def test_scp():
        local_device_name = 'c3560c-12pc-s'
        remote_device_name = 'c2960cx-8pc'

        testbed = load(os.path.join(os.path.dirname(__file__), args.testbed))

        local_device = testbed.devices[local_device_name]

        # startup-configを
        local_path = 'startup-config'

        # 対向装置にこのファイル名で送り込む
        remote_path = f'{local_device_name}.{local_path}'

        # 発行するコマンドはこうなる
        # copy startup-config scp://username:password@192.168.122.252/c3560c-12pc-s.startup-config

        # connect
        local_device.connect()

        # scp
        result = scp_dev_to_dev(local_device=local_device, local_path=local_path, remote_device_name=remote_device_name, remote_path=remote_path)

        # disconnect
        if local_device.is_connected():
            local_device.disconnect()

        return result is True


    def main():

        if args.run:
            test_scp()
            return 0

        parser.print_help()
        return 0

    sys.exit(main())