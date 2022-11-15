# MACアドレス

IEEEからダウンロードするのが正しいがアカウントが必要。

https://regauth.standards.ieee.org/standards-ra-web/pub/view.html#registries


JSON形式でここからダウンロードするのが楽。頻度高く更新している。

https://maclookup.app/downloads/json-database



## GlobalとPrivate

端末のMACアドレスはランダムなプライベートアドレスを利用するようになってきている。

```text
1  2  3  4  5  6
00:00:00:00:00:00
```

前半がベンダーを識別する部分、後半がベンダーによって割り当てられたNICを識別する部分。

先頭の１オクテットのフォーマット

```text
bit7 bit6 bit5 bit4 bit3 bit2 bit1 bit0
                                   0 = unicast
                                   1 = multicast
                               0     = globally unique
                               1     = locally administered
```

先頭の１オクテットをみたときに、奇数であればマルチキャスト、偶数であればユニキャスト、ということがわかる。

例： 01:00:5E は先頭１オクテットが奇数なのでマルチキャスト(IPマルチキャスト)
例： 01:00:0C は先頭１オクテットが奇数なのでマルチキャスト(Cisco独自 PVST/CDP/VTP/UDLD等)
例： 01:80:C2 は先頭１オクテットが奇数なのでマルチキャスト(LLDPやBPDU)
例： 01:1B-19 は先頭１オクテットが奇数なのでマルチキャスト(PTPv2 over Ethernet)
例： 33:33-XX は先頭１オクテットが奇数なのでマルチキャスト(IPv6マルチキャスト)

ユニキャストアドレスのうち、先頭１オクテットが2 or 6 or A or Eで終わるものはローカルアドレスになる。

```text
. . . . 0 0 1 0  = .2
. . . . 0 1 1 0  = .6
. . . . 1 0 1 0  = .A
. . . . 1 1 1 0  = .E
```

これらMACアドレスはいずれもプライベートMACアドレスなので、ベンダーコードを検索しても出てこない。

```text
2e:14:db:b8:9b:d8 先頭1オクテットがEで終わるのでプライベートMACアドレス
fe:dd:b8:3f:de:59 先頭1オクテットがEで終わるのでプライベートMACアドレス
ee:e7:80:e3:c3:b2 先頭1オクテットがEで終わるのでプライベートMACアドレス
7e:87:0b:67:17:e2 先頭1オクテットがEで終わるのでプライベートMACアドレス
12:87:66:76:e7:7d 先頭1オクテットが2で終わるのでプライベートMACアドレス
c6:78:ad:69:2d:fd 先頭1オクテットが6で終わるのでプライベートMACアドレス
26:67:ca:be:bc:c9 先頭1オクテットが6で終わるのでプライベートMACアドレス
f6:ff:cc:5f:51:68 先頭1オクテットが6で終わるのでプライベートMACアドレス
```

iPhone、iPad、iPod touch、Apple Watch でプライベート Wi-Fi アドレスを使う
https://support.apple.com/ja-jp/HT211227

MACアドレスランダム化の実装
https://source.android.com/docs/core/connect/wifi-mac-randomization

ランダム ハードウェア アドレスを使う理由
https://support.microsoft.com/ja-jp/windows/%E3%83%A9%E3%83%B3%E3%83%80%E3%83%A0-%E3%83%8F%E3%83%BC%E3%83%89%E3%82%A6%E3%82%A7%E3%82%A2-%E3%82%A2%E3%83%89%E3%83%AC%E3%82%B9%E3%82%92%E4%BD%BF%E3%81%86%E7%90%86%E7%94%B1-060ad2e9-526e-4f1c-9f3d-fe6a842640ed


## Global Unique アドレスの形式

| IEEE割り当て | 割り当てビット |  アドレス数      | 組織識別 |
| ----------- | ------------- | --------------- | ------- |
| MA-L        |  24           | 2^24 = 約1600万 | OUI     |
| MA-M        |  28           | 2^20 = 約100万  | none    |
| MA-S        |  36           | 2^12 = 4096    | OUI-36   |


たとえば、

00:00:0C はMA-Lなので、この情報だけで組織を識別することができて、ベンダーはCisco。

1C:87:76:D はMA-Mなので組織を表す識別子は含まず、このプレフィクスに限定してQivivoというベンダーに割り当てられている。

00:50:C2:00:0 はMA-SなのでOUI-36そのものであり、組織を識別することができて、ベンダーは'T.L.S. Corp.'という会社になる。

MA-Sの最古の割り当ては'2015/08/29'

MA-Mの最古の割り当ては'2016/02/05'


## フォーマット

オブジェクトの配列。

```json
[
  {
        "macPrefix": "00:00:00",
        "vendorName": "XEROX CORPORATION",
        "private": false,
        "blockType": "MA-L",
        "lastUpdate": "2015/11/17"
   }
]
```

`blockType`の意味は次の通り。

<dl>
  <dt>MA-L</dt>
  <dd>MAC Address Block Large (previously named OUI). Number of address 2^24 (~16 Million)</dd>

  <dt>MA-M</dt>
  <dd>MAC Address Block Medium. Number of address 2^20 (~1 Million)</dd>

  <dt>MA-S</dt>
  <dd>MAC Address Block Small (previously named OUI-36, encompasses IAB Assignments). Number of address 2^12 (4096)</dd>

  <dt>CID</dt>
  <dd>Company Identifier. This prefix will not be used for globally unique applications. Number of address 2^24 (~16 Million)</dd>
</dl>
