#!/usr/bin/env python

import logging
import os

import requests

logger = logging.getLogger(__name__)

URL = 'https://maclookup.app/downloads/json-database/get-db'

save_dir = os.path.join(os.path.dirname(__file__), 'json')
os.makedirs(save_dir, exist_ok=True)


def get(url, requests_options={}):

    logger.info(f'get {url}')

    headers = {'content-type': 'application/json'}

    r = requests.get(url, headers=headers, **requests_options)

    # print(r.headers)
    # {'Date': 'Sun, 06 Nov 2022 07:51:56 GMT',
    #  'Content-Type': 'application/octet-stream',
    #  'Connection': 'keep-alive',
    #  'Cache-Control': 'public, max-age=3600',
    #  'Content-Description': 'File Transfer',
    #  'Content-Disposition': 'attachment; filename="mac-vendors-export.json"',
    #  'Content-Transfer-Encoding': 'binary',
    #  'X-Srv': 'MAC Lookup Frontend [v16.8.10]',
    #  'X-Srv-Id': '3c903eb5-9552-4dd0-bd7f-2db1f49cb078',
    #  'Last-Modified': 'Sun, 06 Nov 2022 07:42:04 GMT',
    #  'CF-Cache-Status': 'HIT',

    content_disposition = r.headers.get('Content-Disposition', 'filename="downloaded.json"')

    filename = content_disposition.split('filename=')[1]
    filename = filename.strip('"')
    filename = filename.strip("'")

    data = parse_response(r)

    if data:
        save_path = os.path.join(save_dir, filename)
        save(save_path, data)


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

        logger.info(f'trying to get {URL}')

        get(URL, requests_options={'timeout': 10})

        return 0


    sys.exit(main())
