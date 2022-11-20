#!/usr/bin/env python

import re

#
# dictフィルタ
#


def filter_func(key: str = '', query: str = '') -> callable:
    """
    辞書型を検索する関数を返却する（単一階層のみ）

    例： 配列に格納されているdictのうち、output_dropsキーが0のものだけを抽出する

    f = filter_func(key='output drops', value_query='[^0]')
    filtered = [d for d in results if f(d)]

    この例だとlambdaでいいじゃん、ってことになってしまうが、次のand_filterで効果を発揮する。

    Arguments:
      key {str} -- 対象のキー
      query {str} -- 対象のキーに対応する値を検索する正規表現文字列

    Returns:
      function -- 辞書型オブジェクトを引数にとり、一致した場合にそれを返却する
    """
    if not key:
        return None

    r = re.compile(r'%s' % query, re.IGNORECASE)

    # この関数を返却する
    # 深い階層まで探索したければこれを改造
    def _filter(d):
        ret = None
        v = d.get(key, '')
        if r.search(v):
            ret = d
        return ret

    return _filter


def and_filter(d: dict, funcs: list) -> dict:
    """
    オブジェクトとフィルタ関数の配列を受け取り、and条件で検索する

    想定する使い方
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


def find_values(d: dict, k: str):
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


def search_list_of_dict(arr: list, k:str, v: str, exact_match=True) -> dict:
    """
    バイナリサーチで辞書型のリストを検索する、リストはkキーの値でソートされていることが前提

    Args:
        arr (list): 辞書型のリスト [{}, {}, {}...]
        k (str): 辞書型のキー
        v (str): kに対応する値
        exact_match (bool, optional): 厳密に一致させるか、文字列を含めば一致とするか. Defaults to True.

    Returns:
        dict: 検索結果
    """

    n = len(arr)
    left = 0
    right = n - 1

    while left <= right:
        center = (left + right) // 2

        if exact_match:
            # 完全一致
            if arr[center].get(k, '') == v:
                return arr[center]
            elif arr[center].get(k) < v:
                left = center + 1
            else:
                right = center - 1
        else:
            # 文字列が含まれていれば一致と判断
            if arr[center].get(k, '').find(v) == 0 or v.find(arr[center].get(k, '')) == 0:
                return arr[center]
            elif arr[center].get(k) < v:
                left = center + 1
            else:
                right = center - 1

    return None


if __name__ == '__main__':

    import sys

    def test_binary_search():

        # MACアドレスのベンダーコードのデータベースから適当に抽出
        test_mac_vendors = [
            {
                "macPrefix": "00:00:0C",
                "vendorName": "Cisco Systems, Inc",
                "blockType": "MA-L",
                "lastUpdate": "2015/11/17"
            },
            {
                "macPrefix": "00:00:0E",
                "vendorName": "FUJITSU LIMITED",
                "blockType": "MA-L",
                "lastUpdate": "2018/10/13"
            },
            {
                "macPrefix": "00:00:1B",
                "vendorName": "Novell, Inc.",
                "blockType": "MA-L",
                "lastUpdate": "2016/04/27"
            },
            {
                "macPrefix": "1C:87:76:D",
                "vendorName": "Qivivo",
                "blockType": "MA-M",
                "lastUpdate": "2016/02/05"
            },
            {
                "macPrefix": "70:B3:D5:91:3",
                "vendorName": "Shenzhen Riitek Technology Co.,Ltd",
                "blockType": "MA-S",
                "lastUpdate": "2016/02/18"
            },
            {
                "macPrefix": "70:B3:D5:41:A",
                "vendorName": "HYOSUNG Heavy Industries Corporation",
                "blockType": "MA-S",
                "lastUpdate": "2022/06/23"
            },
        ]

        # これをソートする
        test_mac_vendors = sorted(test_mac_vendors, key=lambda x: x.get('macPrefix', ''))

        key = 'macPrefix'
        for d in test_mac_vendors:
            mac = d.get(key)
            assert d == search_list_of_dict(test_mac_vendors, key, mac)

        assert search_list_of_dict(test_mac_vendors, key, '00:00:0F') is None


    def main():
        test_binary_search()
        return 0

    sys.exit(main())
