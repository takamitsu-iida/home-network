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
