#!/usr/bin/env python

"""
json/mac-vendors-export.jsonからMACアドレスを検索する。
"""

import logging
import os
import json

logger = logging.getLogger(__name__)

#
# tinydb
#
from tinydb import TinyDB, Query #, where

db_dir = os.path.join(os.path.dirname(__file__), 'json')
db_file = 'db.json'
db_path = os.path.join(db_dir, db_file)


if __name__ == '__main__':

    import argparse
    import sys

    from pprint import pprint

    # default setting
    logging.basicConfig(level=logging.INFO)

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--filename',
            dest='filename',
            help='json filename',
            type=str,
            default='json/mac-vendors-export.json',
        )
        args, _ = parser.parse_known_args()



        if not os.path.exists(db_path):

            json_path = os.path.join(os.path.dirname(__file__), args.filename)
            with open(json_path) as f:
                d = json.load(f)

            with TinyDB(db_path) as db:
                db.insert_multiple(d)

        with TinyDB(db_path) as db:
            q = Query()

            pprint(db.search(
                (q.macPrefix == '00:00:0C')
            ))

    sys.exit(main())
