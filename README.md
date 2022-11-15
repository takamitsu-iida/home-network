# 自宅ネットワーク環境


## 管理基盤のセットアップ

`~/.pyats/pyats.conf` を作成して、暗号キーを記載する。ファイルのモードは600にする。

```bash
[secrets]

string.representer = pyats.utils.secret_strings.FernetSecretStringRepresenter
string.key = ...
```

## python仮想環境

Pythonの仮想環境を構築する。

```bash
python -m venv .venv
```

direnvをインストール済みなら、.envrcはリポジトリに含まれるので以下のようにする。

```bash
direnv allow
```

pythonのモジュールをインストールする。

```bash
pip install -r requirements.txt
```

### node.js

WSL環境にnode.jsをインストールする手順はマイクロソフトのページに詳しい。

https://learn.microsoft.com/ja-jp/windows/dev-environment/javascript/nodejs-on-wsl



<br><br>

# MACアドレス調査


```text
MACアドレス a0:c9:a0:9a:7f:01
SSID taka 11ac
AP名taka-AP1815I (Ch 136)
最も近いAP ayane-CAP702I(-84 dBm) living-AP1815M(-70 dBm)
デバイスタイプ Android-Samsung-Galaxy-Phone-S8
パフォーマンス信号強度: -38 dBm
信号品質: 54 dB
接続速度: 173 Mbps
チャネル幅: 20 MHz
機能
802.11ac (5GHz)空間ストリーム: 2
Cisco Compatibleサポート対象(CCX v4)
```
