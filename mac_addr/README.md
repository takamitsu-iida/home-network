# MACアドレス

JSON形式でここからダウンロードできる

https://maclookup.app/downloads/json-database


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
