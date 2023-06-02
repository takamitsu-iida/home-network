#!/usr/bin/env python

#
# FreeRadiusのアカウンティングログを検索します。
#

import logging
import re
import sys
import time
import typing
from datetime import datetime
from pathlib import Path

import schedule
import yaml
from tabulate import tabulate


# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

# データ用ディレクトリ
data_dir = app_home.joinpath('data')

# libフォルダにおいたpythonスクリプトをインポートできるようにするための処理
# このファイルの位置から一つ
lib_dir = app_home.joinpath('lib')
if lib_dir not in sys.path:
    sys.path.append(str(lib_dir))

# lib/daemon_util/daemon_util.py
from daemon_util import SingleDaemon

#
# logディレクトリ
#
log_file = app_path.with_suffix('.log').name
log_dir = app_home.joinpath('log')
log_dir.mkdir(exist_ok=True)

# ログファイルのパス
log_path = log_dir.joinpath(log_file)

logger = logging.getLogger(__name__)

# ログレベル設定
logger.setLevel(logging.INFO)

# フォーマット
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 標準出力へのハンドラ
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# ログファイルのハンドラ
file_handler = logging.FileHandler(log_path, 'a+')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

#
# 既知デバイスのファイル
#
KNOWN_DEVICES_FILE = 'known_devices.yaml'
KNOWN_DEVICES_PATH = app_home.joinpath(KNOWN_DEVICES_FILE)


#
# freeRadiusのアカウンティングログの場所
# デフォルトの設定では日付ごとのファイル名が生成されますが、設定を変更してdetail.logで固定しています。
# logrotateで日付ごとにローテーションされます。
#
DEFAULT_RADACCT_FILES = ['/opt/homebrew/var/log/radius/radacct/192.168.122.253/detail.log']


def find_values(d: dict, k: str) -> typing.Iterator[typing.Tuple]:
    """
    辞書型を探索してkeyに対応する値をyieldする

    使い方
    print(list(find_values(d, 'id')))

    Args:
        d (dict): dict
        k (str): key

    Yields:
        object: value
    """
    if isinstance(d, list):
        for i in d:
            for x in find_values(i, k):
                yield x
    elif isinstance(d, dict):
        if k in d:
            yield d[k]
        for j in d.values():
            for x in find_values(j, k):
                yield x


def find_first_value(d: dict, k: str) -> object:
    """
    辞書型を探索して最初に見つけたkeyに対応する値を返却する

    使い方
    print(find_first_value(d, 'id'))

    Args:
        d (dict): dict
        k (str): key

    Yields:
        object: value
    """
    for v in find_values(d, k):
        return v


def filter_func(key: str = '', query: str = '') -> typing.Callable:
    """
    辞書型を検索する関数を返却する（単一階層のみ）

    使い方の例： 配列に格納されているdictのうち、output_dropsキーが0のものだけを抽出する

    f = filter_func(key='output drops', query='[^0]')
    filtered = [d for d in results if f(d)]

    Arguments:
      key {str} -- 対象のキー
      query {str} -- 対象のキーに対応する値を検索する正規表現文字列

    Returns:
      function -- 辞書型オブジェクトを引数にとり、一致した場合はその辞書型オブジェクトを返却する
    """
    if not key:
        return None

    try:
        regex = re.compile(query, re.IGNORECASE)
    except re.error as e:
        logger.error(f'{str(e)}, query={query}')
        return None

    # ここで定義した関数を返却する
    def _filter(d):
        # 辞書型を探索して最初に見つけた値がqueryと一致するか
        v = str(find_first_value(d, key))
        return d if regex.search(v) else None

    return _filter


def and_filter(d: dict, funcs: list) -> dict:
    """
    オブジェクトとフィルタ関数の配列を受け取り、and条件で検索する

    使い方の例：
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


def load_yaml(file_path: str) -> dict:
    """
    YAMLファイルを読み取って辞書型にして返却する

    Args:
        file_path (str): YAMLファイルのパス

    Returns:
        dict: 読み取ったデータ
    """
    try:
        with open(file_path) as f:
            try:
                d = yaml.safe_load(f)
                return d
            except yaml.YAMLError as e:
                logger.error(e)
    except OSError as e:
        logger.error(e)
    return None


def get_known_mac_addresses(known_device_file: str = KNOWN_DEVICES_PATH) -> list:
    """
    KNOWN_DEVICES_PATHに指定されたパスのYAMLファイルをロードして、'mac'キーの値をリストにして返却する

    Args:
        known_device_file (str, optional): YAMLファイルのパス. Defaults to KNOWN_DEVICES_PATH.

    Returns:
        list: 全ての'mac'キーの値をリストにして返却
    """
    # known_devices.yamlをロードする
    known_devices = load_yaml(known_device_file)
    if known_devices is None:
        logger.error(f'known device not found in : {KNOWN_DEVICES_PATH}')
        return []

    # 辞書型の中にある'mac'キーの値を全て取り出して返却する
    known_mac_list = list(find_values(known_devices, 'mac'))

    # 大文字に変換
    known_mac_list = [string.upper() for string in known_mac_list]

    return known_mac_list


def parse_timestamp(candidate: str) -> datetime:
    """時刻の文字列からdatetimeオブジェクトを返却します。

    想定する時刻の文字列
    Fri May 26 18:53:29 2023

    Args:
        candidate (str): iso形式の時刻

    Raises:
        ValueError: datetime.fromisoformat()でパースできなかった場合にValueErrorをraiseします

    Returns:
        datetime: 変換したdatetime型オブジェクト
    """

    if isinstance(candidate, datetime):
        return candidate

    if isinstance(candidate, str):
        try:
            # strptimeで使う書式コードはここを参照
            # https://docs.python.org/ja/3/library/datetime.html#strftime-strptime-behavior
            return datetime.strptime(candidate, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            logger.error(f'Invalid date format: {candidate}')
            raise ValueError(f'Invalid date format: {candidate}')


def radacct_split_block(path: Path) -> typing.Iterator[typing.Tuple]:
    with path.open(mode='rt') as f:
        datetime_line = ''
        blocks = []
        for line in f:
            if line.strip() == '':
                if datetime_line == '':
                    continue
                yield datetime_line, blocks
                datetime_line = ''
                blocks = []
                continue
            if re.match(r'\s', line):
                blocks.append(line.strip())
            else:
                datetime_line = line.strip()


def radacct_split_key_value(line: str) -> typing.Tuple[str, str]:
    splitted = line.split('=')
    if len(splitted) == 2:
        key = splitted[0].strip()
        value = splitted[1].strip()
        if value.startswith('\"'):
            value = value[1:]
        if value.endswith('\"'):
            value = value[:-1]
        return key, value
    return None, None


def radacct_parse_file(path: Path) -> list:

    # Sat May 27 14:19:14 2023
    # 	User-Name = "f6-ff-cc-5f-51-68"
    # 	NAS-Port = 1
    # 	NAS-IP-Address = 192.168.122.253
    # 	Framed-IP-Address = 192.168.122.118
    # 	Framed-IPv6-Prefix = fe80::/64
    # 	Framed-IPv6-Prefix = 2400:2411:561:5b00::/64
    # 	NAS-Identifier = "AIR-AP1815M-Q"
    # 	Airespace-Wlan-Id = 1
    # 	Acct-Session-Id = "646f26a4/f6:ff:cc:5f:51:68/911"
    # 	NAS-Port-Type = Wireless-802.11
    # 	Cisco-AVPair = "audit-session-id=fd7aa8c000000311a4266f64"
    # 	Acct-Authentic = Remote
    # 	Event-Timestamp = "May 27 2023 14:19:14 JST"
    # 	Acct-Status-Type = Interim-Update
    # 	Acct-Input-Octets = 15848837
    # 	Acct-Input-Gigawords = 0
    # 	Acct-Output-Octets = 129251932
    # 	Acct-Output-Gigawords = 0
    # 	Acct-Input-Packets = 76685
    # 	Acct-Output-Packets = 120928
    # 	Acct-Session-Time = 158765
    # 	Acct-Delay-Time = 0
    # 	Calling-Station-Id = "192.168.122.118"
    # 	Called-Station-Id = "192.168.122.253"
    # 	Acct-Unique-Session-Id = "3f6f99119089c6176f2b00a843d649c9"
    # 	Timestamp = 1685164754

    logger.info(f'parse {str(path)}')

    parsed_list = []
    for _datetime_line, blocks in radacct_split_block(path):
        d = {}
        for line in blocks:
            key, value = radacct_split_key_value(line)
            if key is None:
                continue
            d[key] = value

        # Acct-Session-Idキーを持たないものは、通常とは違うアカウンティングログなので無視する
        if 'Acct-Session-Id' not in d:
            continue

        # 配列に格納する
        parsed_list.append(d)

    # 'Acct-Session-Id' キーの値でソートしておく
    parsed_list.sort(key=lambda x: x['Acct-Session-Id'])

    return parsed_list



def radacct_parse_files(log_files: list) -> list:
    """_summary_

    Args:
        log_files (list): ファイルのパス文字列が格納されたリスト

    Returns:
        list: _description_
    """

    parsed = []
    for log_file in log_files:
        path = Path(log_file)
        if not path.exists():
            continue
        parsed.extend(radacct_parse_file(path))

    return parsed


def tabulate_json_list_brief(json_list: list):

    tabulate_list = []
    for d in json_list:
        username = d.get('User-Name', '-')
        wlan = d.get('Airespace-Wlan-Id', '-')
        timestamp = d.get('Event-Timestamp', '-')
        status = d.get('Acct-Status-Type', '-')

        tabulate_list.append([username, wlan, timestamp, status])

    return tabulate(tabulate_list, headers=['User-Name', 'Wlan-Id', 'Timestamp', 'Status'], tablefmt='github')



def detect_unknown_user_name(log_files: list) -> list:

    # 既知のMACアドレスを調べる
    known_mac = get_known_mac_addresses()

#    unknown_mac = []
#    for client in wlc_clients:
#        mac = client.get('mac_address', None)
#        if mac is None:
#            continue
#        mac = mac.upper()
#        if mac not in known_mac:
#            unknown_mac.append(client)
#    return unknown_mac


def run_func(log_files: list) -> callable:

    # 一度通知したものはここに格納して、次からは発報しない
    reported_mac = []

    # この関数を返却する
    def _run():
        logger.info('parse radacct')
        radacct_parse_files(log_files=log_files)

    return _run


def run_schedule(func: callable):
    """
    scheduleモジュールを利用して定期実行する

    schedule.every(1).minutes.do(dummy, args, kwargs)  # 毎分実行
    schedule.every(1).hours.do(dummy, args, kwargs)    # 毎時実行
    schedule.every().hour.at(':30').do(dummy)          # 毎時30分時点で実行
    schedule.every().minute.at(':30').do(dummy)        # 毎分30秒時点で実行
    schedule.every().day.at('12:10').do(dummy)         # 毎日12時10分時点で実行

    Args:
        ip (str): 対象装置のIPアドレス
        username (str): 対象装置のログインユーザ名
        password (str): 対象装置のログインパスワード
    """

    # 10分ごとに実行
    schedule.every(10).minutes.do(func)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except SystemExit:
            break
        except Exception as e:
            logger.info(e)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='detect unknown device')
    parser.add_argument('-t', '--test', action='store_true', help='test run')
    parser.add_argument('-f', '--files', nargs='*', dest='log_files', default=DEFAULT_RADACCT_FILES, help='Path to one or more file to parse.')
    parser.add_argument('-d', '--daemon', action='store_true', default=False, help='run as daemon')
    parser.add_argument('-k', '--kill', action='store_true', default=False, help='kill running daemon')
    parser.add_argument('-c', '--clear', action='store_true', default=False, help='clear junk pid file')
    args = parser.parse_args()

    log_files = args.log_files

    def main():

        # PIDファイルはlogディレクトリに保存
        pid_dir = app_home.joinpath('log')
        pid_file = pid_dir.joinpath(app_name + '.pid')

        if args.test:
            parsed = radacct_parse_files(log_files=log_files)
            print(tabulate_json_list_brief(parsed))

            return 0

        if args.clear:
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.clear()
            return 0

        if args.kill:
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.stop_daemon()
            return 0

        if args.daemon:
            logger.info(f'{__file__} started')
            d = SingleDaemon(pid_dir=pid_dir, pid_file=pid_file)
            d.add_presereved_handlers(file_handler)  # ファイルハンドラを閉じないように指定
            d.start_daemon(run_schedule, run_func(log_files))
            return 0

        parser.print_help()
        return 0

    sys.exit(main())
