#!/usr/bin/env python

import logging
import os

#
# import pyATS module
#
from pyats.utils.secret_strings import to_plaintext
from pyats.topology.bases import TopologyDict
from genie.testbed import load
from genie.libs.conf.testbed import Testbed
from genie.metaparser.util.exceptions import SchemaEmptyParserError
from unicon.core.errors import TimeoutError, StateMachineError, ConnectionError
from unicon.core.errors import SubCommandFailure
from unicon.eal.dialogs import Dialog, Statement

logger = logging.getLogger(__name__)


def get_testbed_from_file(testbed_filename: str) -> Testbed:
    try:
        testbed_path = os.path.join(os.path.dirname(__file__), testbed_filename)
        testbed = load(testbed_path)
    except:
        return None

    return testbed


def get_testbed_devices(testbed_filename: str) -> TopologyDict:
    testbed = get_testbed_from_file(testbed_filename=testbed_filename)
    if testbed is not None:
        return testbed.devices
    return None


def get_inventory(testbed: Testbed, device_name: str):
    """
    pyATSのテストベッドからインベントリ情報を抽出して返却する

    動作条件
    テストベッドのconnectionsにdefaultsとviaが設定されていること

    connections:
      defaults:
        via: ssh

    Args:
        testbed_filename (str): テストベッドのファイル名（ディレクトリ含まず）
        device_name (str): デバイス名

    Returns:
        dict: {'ip': xxx, 'username': xxx, 'password': xxx}
    """

    dev = testbed.devices[device_name]

    # connectionsの中からdefaultsを取り出す
    conn_defaults = dev.connections.get('defaults', None)
    if conn_defaults is None:
        username, password = dev.api.get_username_password()
    else:
        # defaltsコネクションで指定されたvia指定を取り出す
        via = conn_defaults.get('via', None)
        if via is None:
            username, password = dev.api.get_username_password()
        else:
            # viaで指定されたコネクション情報を取り出す
            conn = dev.connections.get(via, None)
            if conn is None:
                username, password = dev.api.get_username_password()
            else:
                # コネクションに設定されたcredentialsを取り出す
                cred = conn.get('credentials', {}).get('default', None)
                if cred is None:
                    username, password = dev.api.get_username_password()
                else:
                    username = cred.get('username', '')
                    password = to_plaintext(cred.get('password', ''))

    if conn is None:
        ip = ''
    else:
        ip = str(conn.get('ip', ''))

    d = {'ip': ip, 'username': username, 'password': password}

    return d


def parse_command(dev, command: str):
    # connect
    if not dev.is_connected():
        try:
            dev.connect()
        except (TimeoutError, StateMachineError, ConnectionError) as e:
            logger.error(str(e))
            return None

    # parse
    try:
        parsed = dev.parse(command)
    except (SubCommandFailure, SchemaEmptyParserError) as e:
        logger.error(str(e))
        return None

    # disconnect
    if dev.is_connected():
        dev.disconnect()

    return parsed


if __name__ == '__main__':

    import argparse
    import sys
    from pprint import pprint

    logging.basicConfig(level=logging.INFO)

    # yapf: disable
    parser = argparse.ArgumentParser(description='test for pyats_util.py')
    parser.add_argument('-t', '--testbed', dest='testbed', help='testbed YAML file', type=str, default='home.yaml')
    parser.add_argument('-d', '--device', dest='device', help='device name', type=str, default='uut')
    parser.add_argument('-i', '--inventory', action='store_true', default=False, help='get inventory info')
    args = parser.parse_args()
    # yapf: enable


    def main():
        if args.inventory:
            testbed = get_testbed_from_file(testbed_filename=args.testbed)
            inventory = get_inventory(testbed=testbed, device_name=args.device)
            pprint(inventory)
            return 0

        parser.print_help()
        return 0

    sys.exit(main())