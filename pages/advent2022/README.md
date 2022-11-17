（このページはAdvent Calendar 2022向けに記載したものです）

# 自宅のネットワークに接続している端末のMACアドレスを調べてみた


テレワーク主体の働き方になってから、自宅のネットワーク環境を強化しているのですが、
設計書を書くほどのものではないですし、管理の手間をかけているわけでもありません。

<br>

はっきりいって <span style="font-size: 200%;">無法地帯</span> です。

<br>

自宅のネットワークに何が接続しているのか、たまには調べてみようと思います。

<br><br>

## 自宅のネットワーク

こんな感じです。

![topology](img/topology.svg)

インターネットはソフトバンク光を契約しています。

ソフトバンク光のルータ（光ＢＢユニット）にPoE対応のCat3560を接続して、そこから2台のAironetに給電しています。

Cat3560の先にもう1台Cat2960がいて、その周辺がテレワーク環境になっています。

特別なことは何もない、ごく普通の環境です。

<br>

## DHCPサーバの情報を採取

IPアドレスはソフトバンクのルータからDHCPで払いだされます。

IPアドレスがなければ通信できませんので、DHCPサーバが払いだしているIPアドレスの情報がわかれば、接続している端末の多くは把握できそうです。

![DHCP](img/fig1.png)

この情報を取りたいわけですが、ソフトバンク光のルータは機種が古いこともあって、APIでの情報採取はおろか、SSHでの接続もできません。

<span style="font-size: 200%;">接続プロトコルはHTTP、認証はベーシック認証</span> です。HTTPSですらありません。

仕方ないのでPythonのrequestsモジュールで該当ページに接続してスクレイピングすることにします。

これでIPアドレスとMACアドレスの対応がわかりますので、あとはMACアドレスのベンダーコードをみて何かを推察してみます。

<br>

## 分析してみた

こちらのサイトからMACアドレスのベンダー情報をダウンロードさせていただきました。

https://maclookup.app/downloads/json-database

このMACアドレスのベンダーコードのJSONデータベースを使って、自宅LANにいるMACアドレスを検索してみました。

その結果がこちら。

| mac               | ip              | vendor                                 |
|-------------------|-----------------|----------------------------------------|
| 5E:54:72:B7:19:9F | 192.168.122.103 |                                        |
| 28:84:FA:EA:5F:0C | 192.168.122.106 | SHARP Corporation                      |
| 04:03:D6:D8:57:5F | 192.168.122.107 | Nintendo Co.,Ltd                       |
| 3C:22:FB:7B:85:0E | 192.168.122.109 | Apple, Inc.                            |
| 0C:D2:92:F9:0B:73 | 192.168.122.110 | Intel Corporate                        |
| 2E:14:DB:B8:9B:D8 | 192.168.122.111 |                                        |
| FE:DD:B8:3F:DE:59 | 192.168.122.112 |                                        |
| 4C:34:88:93:80:87 | 192.168.122.113 | Intel Corporate                        |
| 44:65:0D:DA:2A:F5 | 192.168.122.114 | Amazon Technologies Inc.               |
| 68:84:7E:87:04:BE | 192.168.122.115 | FUJITSU LIMITED                        |
| EE:E7:80:E3:C3:B2 | 192.168.122.116 |                                        |
| 7E:87:0B:67:17:E2 | 192.168.122.118 |                                        |
| 20:DF:B9:B4:BC:79 | 192.168.122.119 | Google, Inc.                           |
| 38:1A:52:5B:42:15 | 192.168.122.156 | Seiko Epson Corporation                |
| A4:5E:60:E4:1A:DD | 192.168.122.120 | Apple, Inc.                            |
| C6:78:AD:69:2D:FD | 192.168.122.121 |                                        |
| 12:87:66:76:E7:7D | 192.168.122.122 |                                        |
| A0:C9:A0:9A:7F:01 | 192.168.122.130 | Murata Manufacturing Co., Ltd.         |
| 90:9A:4A:D6:BB:B9 | 192.168.122.159 | TP-LINK TECHNOLOGIES CO.,LTD.          |
| 08:97:98:04:22:E4 | 192.168.122.160 | COMPAL INFORMATION (KUNSHAN) CO., LTD. |
| F6:FF:CC:5F:51:68 | 192.168.122.172 |                                        |
| 50:EB:F6:95:8B:37 | 192.168.122.174 | ASUSTek COMPUTER INC.                  |
| 90:B6:86:CF:B7:BA | 192.168.122.176 | Murata Manufacturing Co., Ltd.         |
| 84:5C:F3:48:FF:30 | 192.168.122.169 | Intel Corporate                        |
| 26:67:CA:BE:BC:C9 | 192.168.122.123 |                                        |
| 54:3D:1F:FA:CB:6F | 192.168.122.145 |                                        |
| AC:29:3A:C5:D7:8C | 192.168.122.146 | Apple, Inc.                            |
| E6:02:29:6F:AE:FE | 192.168.122.149 |                                        |

28個のMACアドレスのうち11個、すなわち３９％は製造元不明という結果でした。

製造元不明って・・・　これはいったいどういうことでしょう？

<br>

## ランダムMACアドレス

最近のandroidやiOSは無線LANに接続する際にランダムなMACアドレスを使うんだそうです。

この辺りが参考になります。

iPhone、iPad、iPod touch、Apple Watch でプライベート Wi-Fi アドレスを使う

https://support.apple.com/ja-jp/HT211227

MACアドレスランダム化の実装

https://source.android.com/docs/core/connect/wifi-mac-randomization

ランダムといっても無線LANに接続するたびに変わるわけではなく、接続先ごとに一度使うMACアドレスを決めたら変わることはないようです。
このときに使われるMACアドレスは「プライベートMACアドレス」と呼ばれるものになります。

<br>

## プライベートMACアドレスとは

MACアドレスの先頭1オクテットはそのアドレスがどういう種別のものなのかを表す重要な部分です。

```text
bit7 bit6 bit5 bit4 bit3 bit2 bit1 bit0
                                   0 = unicast
                                   1 = multicast
                               0     = globally unique
                               1     = locally administered
```

下一桁の部分は、そのMACアドレスがユニキャストなのか、マルチキャストなのかを表します。このビットが1だとマルチキャストです。

つまり <span style="font-size: 200%;">先頭1オクテットが奇数の場合はマルチキャストMACアドレス</span> と言うことができます。

代表的なマルチキャストMACドレスにはこのようなものがあります。

例： 01:00:5E は先頭１オクテットが奇数なのでマルチキャスト(IPマルチキャスト)
例： 01:00:0C は先頭１オクテットが奇数なのでマルチキャスト(Cisco独自 PVST/CDP/VTP/UDLD等)
例： 01:80:C2 は先頭１オクテットが奇数なのでマルチキャスト(LLDPやBPDU)
例： 01:1B-19 は先頭１オクテットが奇数なのでマルチキャスト(PTPv2 over Ethernet)
例： 33:33-XX は先頭１オクテットが奇数なのでマルチキャスト(IPv6マルチキャスト)

先頭1オクテットが偶数の場合はユニキャストになりますが、さらにその中でも下二桁目のビットが1の場合はプライベートMACアドレスになります。

ここが1ということは、先頭1オクテットの数字は2か6かAかEで終わることになります。

```text
. . . . 0 0 1 0  = ?2
. . . . 0 1 1 0  = ?6
. . . . 1 0 1 0  = ?A
. . . . 1 1 1 0  = ?E
```

先ほど製造元が不明だったMACアドレスを抜き出して整理するとこうなります。

| 5E:54:72:B7:19:9F | 192.168.122.103 | 先頭1オクテットがEで終わるのでプライベートMACアドレス |
| 2E:14:DB:B8:9B:D8 | 192.168.122.111 | 先頭1オクテットがEで終わるのでプライベートMACアドレス |
| FE:DD:B8:3F:DE:59 | 192.168.122.112 | 先頭1オクテットがEで終わるのでプライベートMACアドレス |
| EE:E7:80:E3:C3:B2 | 192.168.122.116 | 先頭1オクテットがEで終わるのでプライベートMACアドレス |
| 7E:87:0B:67:17:E2 | 192.168.122.118 | 先頭1オクテットがEで終わるのでプライベートMACアドレス |
| 12:87:66:76:E7:7D | 192.168.122.122 | 先頭1オクテットが2で終わるのでプライベートMACアドレス |
| C6:78:AD:69:2D:FD | 192.168.122.121 | 先頭1オクテットが6で終わるのでプライベートMACアドレス |
| F6:FF:CC:5F:51:68 | 192.168.122.172 | 先頭1オクテットが6で終わるのでプライベートMACアドレス |
| 26:67:CA:BE:BC:C9 | 192.168.122.123 | 先頭1オクテットが6で終わるのでプライベートMACアドレス |
| E6:02:29:6F:AE:FE | 192.168.122.149 | 先頭1オクテットが6で終わるのでプライベートMACアドレス |
| 54:3D:1F:FA:CB:6F | 192.168.122.145 | これは何？                                         |

先頭1オクテットがEか2か6で終わっているものはプライベートMACアドレスなので、AndroidもしくはiOSの装置と思われます。

って、10台もいるの？

どのMACがどのスマホなのかを調べたくなりますが、プライベートMACアドレスなので製造元すらわかりません。

さらに、1個だけプライベートMACアドレスではないのに、製造元が不明なものがありますね。

これは何だろう？　気持ち悪いですね。

<br>

## MACアドレスのベンダー名だけでは分からない物はどうする？

ベンダー名をみて物が何か類推できるものもあれば、そうでないものもあります。
NintendoとかApple、FUJITSUなんかは分かりやすいです。心当たりあります。

分かるもの

- Nintendo Co.,Ltd はSwitchもしくはWIIです。
- Apple, Inc. はMacBookですね。2台あります。
- Amazon Technologies Inc. はテレビのHDMIに差し込んでるやつかな。
- FUJITSU LIMITED は会社のPCです。
- Google, Inc. はGoogle Home Miniです。
- Seiko Epson Corporation はプリンタだと思います。
- TP-LINK TECHNOLOGIES CO.,LTD. は電源をスマホでON-OFFするやつです。
- ASUSTek COMPUTER INC. は自作PCです。

分からないもの

- SHARP Corporation は何だろう？
- Intel Corporate は漠然としすぎてわからないなぁ。複数あるし。
- Murata Manufacturing Co., Ltd. は村田製作所ですね。物は想像つかないです。
- COMPAL INFORMATION (KUNSHAN) CO., LTD. は何だろう？

ということで<span style="font-size: 200%;">ベンダーコードだけで物を特定するのは困難</span>だということを改めて痛感しました。

ところで自宅の無線LANに使っているAironetはMobility Expressという無線LANコントローラの機能を持っています。

![WLC](img/fig2.png)

この画面の通り、接続している無線LAN端末のホスト名やOSの種類まで特定してくれています。

仕組みはどうやってるのか分かりませんが、有益な情報なのでこの情報も採取して、分析に加えてみましょう。

無線LANコントローラからAPIで情報を採取できるとよかったのですが、やり方が分かりませんでしたので、手っ取り早くPythonのNetmikoモジュールを使ってコマンドで採取してみます。

`show client summary` というコマンドでMACアドレスの一覧が手に入ります。

```bash
(Cisco Controller) >show client summary

Number of Clients................................ 15

Number of EoGRE Clients.......................... 0

                                                                RLAN/
MAC Address       AP Name                        Slot Status        WLAN  Auth Protocol         Port Wired Tunnel  Role
----------------- ------------------------------ ---- ------------- ----- ---- ---------------- ---- ----- ------- ----------------
04:03:d6:d8:57:5f living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
08:97:98:04:22:e4 living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
20:df:b9:b4:bc:79 taka-AP1815I                    1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
2e:14:db:b8:9b:d8 ayane-CAP702I                   1   Associated     1    Yes   802.11n(5 GHz)   1    N/A   No      Local
38:1a:52:5b:42:15 living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
3c:22:fb:7b:85:0e taka-AP1815I                    1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
44:65:0d:da:2a:f5 living-AP1815M                  0   Associated     2    Yes   802.11n(2.4 GHz) 1    N/A   No      Local
7e:87:0b:67:17:e2 living-AP1815M                  1   Associated     1    Yes   802.11ac(5 GHz)  1    N/A   No      Local
```

さらに `show client detail <MACアドレス>` コマンドを使うとデバイスのタイプ（NintendoWII）等の詳細情報が手に入ります。

```bash
(Cisco Controller) >show client detail 04:03:d6:d8:57:5f
Client MAC Address............................... 04:03:d6:d8:57:5f
Client Username ................................. N/A
Client Webauth Username ......................... N/A
Hostname: .......................................
Device Type: .................................... NintendoWII
AP MAC Address................................... 70:ea:1a:84:16:c0
AP Name.......................................... living-AP1815M
AP radio slot Id................................. 0
Client State..................................... Associated
User Authenticated by ........................... None
Client User Group................................
Client NAC OOB State............................. Access
Wireless LAN Id.................................. 2
Wireless LAN Network Name (SSID)................. taka 11ng
Wireless LAN Profile Name........................ taka 11ng
WLAN Profile check for roaming................... Disabled
Hotspot (802.11u)................................ Not Supported
Connected For ................................... 266 secs
BSSID............................................ 70:ea:1a:84:16:c1
Channel.......................................... 6
IP Address....................................... 192.168.122.107
Gateway Address.................................. 192.168.122.1
```

これら情報も付加して分析した結果がこちら。
