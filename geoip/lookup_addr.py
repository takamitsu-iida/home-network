#!/usr/bin/env python

"""
ip-apiのサービスを利用してIPアドレスからGPS座標を得る。

https://ip-api.com/


無料で利用できるのは45 req/minまで。それを超えるとHTTP 429が戻る。
スロットルする場合には過去の実行履歴を保存する必要があり、面倒なので実装しない。
"""

import logging
import requests

logger = logging.getLogger(__name__)

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


def get_my_location(requests_options={}):

    URL = 'http://ip-api.com/json'

    headers = {'content-type': 'application/json'}

    r = requests.get(URL, headers=headers, **requests_options)

    return parse_response(r)


def get_location_by_ip(ip=None, requests_options={}):

    if ip is None:
        return get_my_location(requests_options=requests_options)

    return get_locations([ip], requests_options=requests_options)


def get_locations(ip_list=None, requests_options={}):

    URL = 'http://ip-api.com/batch'

    headers = {'content-type': 'application/json'}

    r = requests.post(URL, headers=headers, json=ip_list, **requests_options)

    return parse_response(r)



if __name__ == '__main__':

    import argparse
    import sys

    from pprint import pprint

    # default setting
    logging.basicConfig(level=logging.INFO)

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--ip',
            dest='ip',
            help='IPv4 or IPv6 address to be queried',
            type=str,
            default=None,
        )
        args, _ = parser.parse_known_args()

        try:
            # data = get_my_location()
            data = get_location_by_ip(args.ip)
            pprint(data)
        except Exception as e:

            print(str(e))

    sys.exit(main())
