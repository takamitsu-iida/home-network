#!/usr/bin/env python

import logging
import os

import yaml
import requests

from tqdm import tqdm

logger = logging.getLogger(__name__)


def load_rir_stats():
    stats_path = os.path.join(os.path.dirname(__file__), 'rir_stats.yml')
    with open(stats_path) as f:
        stats = yaml.safe_load(f)
        return stats


def get(stats, requests_options={}):
    url = stats.get('url')
    file = stats.get('file')
    url += file

    save_dir = os.path.join(os.path.dirname(__file__), 'csv')
    save_path = os.path.join(save_dir, file)
    os.makedirs(save_dir, exist_ok=True)

    headers = {'content-type': 'application/json'}

    # コンテンツの大きさをheadメソッドで調べる
    file_size = head_content_length(url, requests_options=requests_options)

    if file_size:
        # ファイルサイズがわかったら、ストリームとして受信してプログレスバーを表示

        logger.info(f'size of {file}: {file_size} bytes')
        logger.info(f'get stream from {url}')
        pbar = tqdm(total=file_size, unit="B", unit_scale=True)

        r = requests.get(url, headers=headers, stream=True, **requests_options)

        with open(save_path, mode='wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
                pbar.update(len(chunk))
            pbar.close()

    else:
        # ファイルサイズがわからなければgetメソッドで取得
        logger.info(f'get {url}')
        r = requests.get(url, headers=headers, **requests_options)

        data = parse_response(r)
        save(save_path, data)


def head_content_length(url, requests_options={}):
    logger.info(f'head {url}')
    r = requests.head(url, **requests_options)
    history = r.history
    if history:
        logging.info(f'  history: {history}')
        logging.info(f'  url: {history[0].url}')
        logging.info(f'  status: {history[0].status_code}')

    len = r.headers.get('content-length')

    if len is None:
        logging.info(f'{url} response has no content-length')
        return 0
    return int(len)


def parse_response(r):
    if 'json' in r.headers.get('Content-Type'):
        data = r.json()
    else:
        data = r.text

    if r.status_code == 200:
        return data
    elif r.status_code == 403:
        logger.exception(f'403 Authorization Error: {data}')
    elif r.status_code == 404:
        logger.exception(f'404 Page Not Found: {data}')
    elif r.status_code == 429:
        logger.exception(f'429 Rate Limitted: {data}')

    raise Exception(data)


def save(path, data):
    with open(path, mode='w') as f:
        f.write(data)


if __name__ == '__main__':

    # default setting
    logging.basicConfig(level=logging.INFO)

    import os
    import sys

    def main():

        rir = load_rir_stats()
        for name, stats in rir.items():
            logger.info(f'trying to get {name} stats')
            get(stats, requests_options={'timeout': 10})

        return 0

    sys.exit(main())
