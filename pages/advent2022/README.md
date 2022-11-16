# 自宅ネットワークの端末に不明なMACがいる件

advent calendar 2022



- CatalystのMAC学習テーブルのエージングタイムを1時間に変更

```bash
c2960cx-8pc(config)#mac address-table aging-time 3600
c2960cx-8pc(config)#end
```
