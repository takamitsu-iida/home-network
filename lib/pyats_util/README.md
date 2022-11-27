# pyats_util.py

pyatsを使う際にインポートするモジュールが複数あってややこしいので、それらを気にせずに使いたいときにこれを使います。

コマンドの投げ込み程度ならこれらをインポートするだけで十分です。

```python
from pyats_util import get_testbed_devices, parse_command
```

# ios_embedded_packt_capture.py

IOS組み込みのパケットキャプチャ機能を使うときに利用します。

https://www.cisco.com/c/ja_jp/support/docs/ios-nx-os-software/ios-embedded-packet-capture/116045-productconfig-epc-00.html


EPCではconfigモードではなく、execモードでmonitorコマンドを使います。

打ち込んだmonitorコマンドはshow running-configで見えないので、すごく分かりづらいです。

こういうのはスクリプトにしておいた方が楽です。
