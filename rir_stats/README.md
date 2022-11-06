# RIR統計

rir_stats.ymlに記載の場所に割り当て済みアドレスの情報がある。

どの国に割り当てられているか、程度の情報しかない。


```yaml
---

ARIN:
  url: https://ftp.arin.net/pub/stats/arin/
  file: delegated-arin-extended-latest

RIPE:
  url: https://ftp.ripe.net/ripe/stats/
  file: delegated-ripencc-latest

AFRINIC:
  url: https://ftp.afrinic.net/pub/stats/afrinic/
  file: delegated-afrinic-latest

APNIC:
  url: https://ftp.apnic.net/stats/apnic/
  file: delegated-apnic-latest

LACNIC:
  url: https://ftp.lacnic.net/pub/stats/lacnic/
  file: delegated-lacnic-latest
```

<br>

## ダウンロード

以下のスクリプトでcsvディレクトリにダウンロードする。

```bash
$ ./download_files.py
```

<br>

## ファイルフォーマット

https://www.apnic.net/about-apnic/corporate-documents/documents/resource-guidelines/rir-statistics-exchange-format/#FileFormat

区切り文字を'|'とするCSV形式。

### ヘッダ行

先頭の行がヘッダ。

```text
version|registry|serial|records|startdate|enddate|UTCoffset
```

apnicの場合はこう。

```text
2|apnic|20221106|76029|19830613|20221104|+1000
```

これを読み解くとこのように解釈できる。2022年11月時点で7万6千レコードある。

```yaml
version: 2
registry: apnic
serial: 2022-11-06
records: 76,029
startdate: 1983-06-13
enddate: 2022-11-04
UTCoffset: +1000
```

### サマリ行

row[5]が 'summary' になっていたらサマリ行と判断してよさそう。

```text
registry|*|type|*|count|summary
```

apnicの場合はこう。

```text
apnic|*|asn|*|11683|summary
apnic|*|ipv4|*|50950|summary
apnic|*|ipv6|*|13396|summary
```

これを読み解くとこのように解釈できる。

```yaml
registry: apnic
asn: 11,683
ipv4: 50,950
ipv6: 13,396
```

### レコード行（AS番号）

row[2]が 'asn' になっていたらAS番号の行と判断してよさそう。

```text
registry|cc|type|start|value|date|status[|extensions...]
```

apnicの場合はこう。

```text
apnic|JP|asn|173|1|20020801|allocated
```

これを読み解くとこのように解釈できる。

```yaml
registry: apnic
cc: JP
type: AS番号
start: 173
value: 1
date: 2002-08-01
status: allocated
```

startはAS番号の開始番号。16ビットAS番号であれば0-65535までの数字。それを超えて 4294967296 までの数字なら32ビットAS番号。
ビット数の区別はないので、数字の大きさで判断する。

valueはAS番号の個数。


### レコード行（IPv4）

row[2]が 'ipv4' になっていたらIPv4アドレスの行と判断してよさそう。

apnicの場合はこう。

```text
apnic|AU|ipv4|1.0.0.0|256|20110811|assigned
```

これを読み解くとこのように解釈できる。

```yaml
registry: apnic
cc: AU
type: ipv4
start: 1.0.0.0
value: 256
date: 2011-08-11
status: assigned
```

valueの256はホスト数なので、1.0.0.0～1.0.0.255を意味する。


### レコード行（IPv6）

row[2]が 'ipv6' になっていたらIPv6アドレスの行と判断してよさそう。

apnicの場合はこう。

```text
apnic|JP|ipv6|2001:200::|35|19990813|allocated
```

これを読み解くとこのように解釈できる。

```yaml
registry: apnic
cc: JP
type: ipv6
start: 2001:200::
value: 35
date: 1999-08-13
status: allocated
```

valueはプレフィクスの数。上記の例では2001:200::～2001:2035となる。


# cidr report

実際に流れているルーティング情報の統計。

ipv4 https://www.cidr-report.org/as2.0/

ipv6 https://www.cidr-report.org/v6/as2.0/
