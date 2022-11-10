# 自宅ネットワーク環境


## 管理基盤のセットアップ

`~/.pyats/pyats.conf` を作成して、暗号キーの記載する。ファイルのモードは066にする。

```bash
[secrets]

string.representer = pyats.utils.secret_strings.FernetSecretStringRepresenter
string.key = ...
```

### python

Pythonの仮想環境を構築。

```bash
python -m venv .venv
```

```bash
pip install -r requirements.txt
```

### node.js

https://learn.microsoft.com/ja-jp/windows/dev-environment/javascript/nodejs-on-wsl

<br>

## MACアドレス調査
