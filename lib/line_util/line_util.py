#!/usr/bin/env python

"""
LINE Notifyを使って通知する

https://notify-bot.line.me/ja/

準備

1. LINEアプリでLINE Notifyを友だちに追加
    - 友だち検索で @linenotify を検索して出てきたものを追加

2. ブラウザでLINE Notifyのページにログイン
    - https://notify-bot.line.me/ja/
    - 画面右上の  ログイン  をクリック
    - メールアドレスとパスワードを入力してログイン
    - 画面に表示された認証番号をアプリのLINEに入力
    - ログインが完了すると画面右上が  ログイン  からアカウント名に切り替わる

3. アクセストークンを取得
    - 画面右上のアカウント名をクリック
    - マイページをクリック
    - アクセストークンの発行(開発者向け)が表示される
    - トークンを発行する  ボタンをクリック
    - トークン名は適当に付与　MyApp
    - トークルームは  1:1でLINE Notifyから通知を受け取る  を選択
    - 生成されたトークンを ~/.line_myapp にコピーペースト
"""

import logging
import os

import requests
import yaml

logger = logging.getLogger(__name__)


# LINE Notifyのトークンは ~/.line_token.yaml からロードする
TOKEN_DIR = os.path.expanduser('~')
TOKEN_FILENAME = '.line_token.yaml'
TOKEN_PATH = os.path.join(TOKEN_DIR, TOKEN_FILENAME)

# LINE Notifyのトークンを作成したときの名前
TOKEN_NAME = 'MyApp'


def load_yaml(file_path):
    try:
        with open(file_path) as f:
            try:
                d = yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.error(e)
                return None
    except OSError as e:
        logger.error(e)
        return None
    return d


def get_access_token():
    d = load_yaml(TOKEN_PATH)
    if d is None:
        raise Exception('LINE Notify access token file not found.')

    token = d.get(TOKEN_NAME, None)
    if token is None:
        raise Exception(f'LINE Notify token for {TOKEN_NAME} not found.')

    return token


def send_line_notify(message: str, requests_options={}):

    URL = 'https://notify-api.line.me/api/notify'

    access_token = get_access_token()

    headers = {'Authorization': 'Bearer ' + access_token}

    payload = {'message': message}

    r = requests.post(URL, headers=headers, params=payload, **requests_options)

    r.raise_for_status()



if __name__ == '__main__':

    import argparse
    import sys

    from pprint import pprint

    # default setting
    logging.basicConfig(level=logging.INFO)

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-t',
            '--test',
            dest='test',
            help='send test message',
            type=str,
            default=None,
        )
        args, _ = parser.parse_known_args()

        if args.test:
            send_line_notify(args.test)
            return 0

        parser.print_help()
        return 0


    sys.exit(main())
