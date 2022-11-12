# 自宅ネットワーク環境


## 管理基盤のセットアップ

`~/.pyats/pyats.conf` を作成して、暗号キーを記載する。ファイルのモードは066にする。

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
