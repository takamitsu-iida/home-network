#!/usr/bin/env python

#
# 雑多なお試し用
#

import argparse

from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('--testbed', dest='testbed', help='testbed YAML file', type=str, default='testbed.yaml')
args, _ = parser.parse_known_args()

#
# tinydb
#
from tinydb import TinyDB, Query

db = TinyDB('log/db.json')

#
# pyATS
#

# import Genie
from genie.testbed import load

testbed = load(args.testbed)

uut = testbed.devices['uut']

# connect
uut.connect(via='vty')

parsed = uut.parse('show version')
pprint(parsed)

parsed = uut.parse('show mac address-table')
pprint(parsed)



# disconnect
if uut.is_connected():
    uut.disconnect()
