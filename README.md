# 自宅ネットワーク環境

自宅のネットワーク環境を整備するためのツール群です。

つまりは完全に自分専用、ここにあるものはすべて、将来の自分のためのメモ書きです。

<br>

## 管理基盤のセットアップ

`~/.pyats/pyats.conf` を作成して暗号キーを記載します。ファイルのモードは600にしておきます。

```bash
[secrets]

string.representer = pyats.utils.secret_strings.FernetSecretStringRepresenter
string.key = ...
```

## python仮想環境

Pythonの仮想環境を構築します。

```bash
python -m venv .venv
```

direnvをインストール済みなら、.envrcはリポジトリに含まれていますので、allowするだけです。

```bash
direnv allow
```

pythonのモジュールをインストールします。

```bash
pip install -r requirements.txt
```

### vscode

`lib`ディレクトリにライブラリを置いていますので、そこへの参照をvscodeに追加設定しないと不便です。

vscodeの設定画面で extra path を検索すると

```text
Python > Analysis: Extra Paths
```

という設定項目が出てきますので、「項目を追加」ボタンを押して

```text
lib/
```

を追加します。


### node.js

WSL環境にnode.jsをインストールする手順はマイクロソフトのページに詳しいです。

https://learn.microsoft.com/ja-jp/windows/dev-environment/javascript/nodejs-on-wsl


<br><br>

# MACアドレス調査

binディレクトリにある実行ファイルで調査します。


- collect_dhcp_clients.py
- collect_mac_address_table.py
- collect_mac_vendors.py
- collect_wlc_clients.py
- analyze.py
- detect.py

- show_testbed.py



### Catalystの設定変更

MACアドレスの学習テーブルを定期的に採取するために、CatalystのMAC学習テーブルのエージングタイムを1時間に変更しています。

```bash
c2960cx-8pc(config)#mac address-table aging-time 3600
c2960cx-8pc(config)#end
```
