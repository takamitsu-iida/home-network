# 自宅ネットワーク環境

自宅のネットワーク環境を整備するためのツール群です。

つまりは完全に自分専用、ここにあるものは将来の自分のためのメモ書きです。

## ネットワーク構成図

構成図はvscodeに拡張機能Draw.io Integrationをインストールして作成します。

- docs/nwdiagram.drawio.svg

<br>

### HTMLファイルに取り込むには

ファイルメニュー→埋め込み→HTMLを選びます。ライトボックスを外してから「作成」します。

生成されたHTMLを埋め込んだものがこれ。

[ネットワーク構成図](https://takamitsu-iida.github.io/home-network/nwdiagram.html "ネットワーク構成図")

<br>

### マークダウンに張り込むには

拡張子を.drawio.svgにしておけばvscodeの中で絵を編集しつつ、そのファイルをそのままSVGとしても利用できますので、イメージとして取り込めます。

![構成図](docs/nwdiagram.drawio.svg)


<br>

## 管理基盤のセットアップ

`~/.pyats/pyats.conf` を作成して暗号キーを記載します。ファイルのモードは600にしておきます。

```bash
[secrets]

string.representer = pyats.utils.secret_strings.FernetSecretStringRepresenter
string.key = ...
```

> 参考
>
> https://pubhub.devnetcloud.com/media/pyats/docs/utilities/secret_strings.html

macosの場合、インストールされているOpenSSHのバージョンが新しいため、CatalystとのSSH接続には工夫が必要です。

`~/.ssh/config` に次の設定を加えておきます。

```
Host *
    HostkeyAlgorithms +ssh-rsa
    KexAlgorithms +diffie-hellman-group14-sha1,diffie-hellman-group1-sha1
    Ciphers +aes128-cbc,aes192-cbc,aes256-cbc,3des-cbc,aes128-ctr,aes192-ctr,aes256-ctr
    StrictHostKeyChecking no
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


## インベントリの設置場所

IPアドレスと接続に必要なユーザ名・パスワード等の情報はpyATSのテストベッド形式で `lib/pyats_util/home.yaml` に記述しています。
ユーザ名とパスワードは `pyats secret` コマンドで暗号化済みです。複合するためには `~/.pyats/pyats.conf ` ファイルが必要です。

あの装置の接続パスワードってなんだっけ？　となりがちなので、その場合は以下のスクリプトでテストベッドを復号化して表示します。

```bash
bin/show_testbed.py
```

<br><br>

## プロトコルハンドラ

ブラウザのリンクをクリックしたときのハンドラはレジストリの変更が必要です。

```bash
iida@s400win:~/git/home-network$ tree registry/
registry/
├── win10_64bit_teraterm_ssh.reg
└── win10_64bit_teraterm_telnet.reg
```

vscodeでregistryフォルダを右クリックして、「Explorerで表示 Shift + Alt + R」を選択します。
レジストリファイルをダブルクリックして反映した後、PCを再起動すると、TeraTERMが起動します。


# MACアドレス調査

binディレクトリにある実行ファイルで調査します。

- collect_mac_vendors.py
- collect_dhcp_clients.py
- collect_wlc_clients.py
- collect_mac_address_table.py
- analyze.py
- detect.py


## MACアドレスのベンダーコード

MACアドレスのベンダーコードのデータベースをこちらのサイトからダウンロードします。

https://maclookup.app/downloads/json-database

- collect_mac_vendors.py

```bash
(.venv) iida@s400win:~/git/home-network$ bin/collect_mac_vendors.py
usage: collect_mac_vendors.py [-h] [-d] [-u] [-s SEARCH]

download mac vendors database

optional arguments:
  -h, --help            show this help message and exit
  -d, --dump
  -u, --update
  -s SEARCH, --search SEARCH
                        search MAC address

(.venv) iida@s400win:~/git/home-network$ bin/collect_mac_vendors.py -u
INFO:mac_vendors_util.mac_vendors_util:head https://maclookup.app/downloads/json-database/get-db
INFO:__main__:current timestamp is 1669180470.0
INFO:__main__:stored timestamp is 1668921036.0
INFO:__main__:new data found, try to download.
INFO:mac_vendors_util.mac_vendors_util:get https://maclookup.app/downloads/json-database/get-db
INFO:mac_vendors_util.mac_vendors_util:47449 mac vendors downloaded.
```

-uでダウンロードします。
最後にダウンロードしたものよりも新しいものがサイトにある場合だけダウンロードします。


## DHCPサーバのクライアント情報の採取

ソフトバンクの光BBユニットがDHCPサーバを担っています。
HTTP GETで接続してDHCPの払い出し情報をスクレイピングします。

- bin/collect_dhcp_clients.py

実行例。

```bash
(.venv) iida@s400win:~/git/home-network$ bin/collect_dhcp_clients.py
usage: collect_dhcp_clients.py [-h] [-d] [-k] [-c] [-g]

show dhcp clients

optional arguments:
  -h, --help    show this help message and exit
  -d, --daemon  run as daemon
  -k, --kill    kill running daemon
  -c, --clear   clear junk pid file
  -g, --get     get dhcp clients info

(.venv) iida@s400win:~/git/home-network$ bin/collect_dhcp_clients.py -g
[{'ip': '192.168.122.103', 'mac': '5E:54:72:B7:19:9F'},
 {'ip': '192.168.122.106', 'mac': '28:84:FA:EA:5F:0C'},
 {'ip': '192.168.122.107', 'mac': '04:03:D6:D8:57:5F'},
 {'ip': '192.168.122.109', 'mac': '3C:22:FB:7B:85:0E'},
 {'ip': '192.168.122.111', 'mac': '2E:14:DB:B8:9B:D8'},
 {'ip': '192.168.122.112', 'mac': 'FE:DD:B8:3F:DE:59'},
 {'ip': '192.168.122.113', 'mac': '4C:34:88:93:80:87'},
 {'ip': '192.168.122.114', 'mac': '44:65:0D:DA:2A:F5'},
 {'ip': '192.168.122.116', 'mac': 'EE:E7:80:E3:C3:B2'},
 {'ip': '192.168.122.118', 'mac': '7E:87:0B:67:17:E2'},
 {'ip': '192.168.122.119', 'mac': '20:DF:B9:B4:BC:79'},
 {'ip': '192.168.122.156', 'mac': '38:1A:52:5B:42:15'},
 {'ip': '192.168.122.120', 'mac': 'A4:5E:60:E4:1A:DD'},
 {'ip': '192.168.122.121', 'mac': 'C6:78:AD:69:2D:FD'},
 {'ip': '192.168.122.122', 'mac': '12:87:66:76:E7:7D'},
 {'ip': '192.168.122.125', 'mac': 'BA:97:90:3B:41:7A'},
 {'ip': '192.168.122.130', 'mac': 'A0:C9:A0:9A:7F:01'},
 {'ip': '192.168.122.144', 'mac': '74:75:48:C6:25:06'},
 {'ip': '192.168.122.146', 'mac': 'AC:29:3A:C5:D7:8C'},
 {'ip': '192.168.122.151', 'mac': 'BE:99:E6:5E:E0:ED'},
 {'ip': '192.168.122.159', 'mac': '90:9A:4A:D6:BB:B9'},
 {'ip': '192.168.122.160', 'mac': '08:97:98:04:22:E4'},
 {'ip': '192.168.122.172', 'mac': 'F6:FF:CC:5F:51:68'},
 {'ip': '192.168.122.174', 'mac': '50:EB:F6:95:8B:37'}]
```

-dでデーモンとして動作し、１時間に一度この情報を採取してtinydbに格納します。

-kでデーモンを停止します。

PCを再起動したり、killコマンドでプロセスを停止するとpidファイルが残存して、次回以降デーモンとして動けなくなります。
その場合は-cでpidファイルを削除するか、logディレクトリにあるpidファイルを削除します。


## Wireless LAN Controllerのクライアント情報の採取

Aironet Mobility Expressが持つ無線LANコントローラ機能から接続クライアントの情報を採取します。

PythonのNetmikoモジュールを使ってWLCに接続して、コマンドを実行、パースしてデータベースに保存します。

- bin/collect_wlc_clients.py

実行例。

```bash
(.venv) iida@s400win:~/git/home-network$ bin/collect_wlc_clients.py
usage: collect_wlc_clients.py [-h] [-d] [-k] [-c] [-g]

show wlc clients

optional arguments:
  -h, --help    show this help message and exit
  -d, --daemon  run as daemon
  -k, --kill    kill running daemon
  -c, --clear   clear junk pid file
  -g, --get     get mac address table info
(.venv) iida@s400win:~/git/home-network$
```

-dでデーモンとして動作し、１時間に一度この情報を採取してtinydbに格納します。

-kでデーモンを停止します。

PCを再起動したり、killコマンドでプロセスを停止するとpidファイルが残存して、次回以降デーモンとして動けなくなります。
その場合は-cでpidファイルを削除するか、logディレクトリにあるpidファイルを削除します。

## CatalystのMAC学習テーブルの情報採取

固定でIPアドレスを割り当てたり、IPv6のみで通信するデバイスは、DHCPサーバの情報では把握できません。
CatalystのMAC学習テーブルを使ってそれらデバイスのMACアドレス情報を採取します。

- bin/collect_mac_address_table.py

```bash
(.venv) iida@s400win:~/git/home-network$ bin/collect_mac_address_table.py
usage: collect_mac_address_table.py [-h] [--testbed TESTBED] [-d] [-k] [-c] [-g]

show mac address table

optional arguments:
  -h, --help         show this help message and exit
  --testbed TESTBED  testbed YAML file
  -d, --daemon       run as daemon
  -k, --kill         kill running daemon
  -c, --clear        clear junk pid file
  -g, --get          get mac address table info
```

## 分析

データベースに格納された情報を使って検知したMACアドレスに関する情報を表示します。

- bin/analyze.py

```bash
(.venv) iida@s400win:~/git/home-network$ bin/analyze.py
usage: analyze.py [-h] [-d] [-w] [-c] [-s SEARCH]

optional arguments:
  -h, --help            show this help message and exit
  -d, --dhcp            show mac from dhcp
  -w, --wlc             show mac from wlc
  -c, --catalyst        show mac from catalyst
  -s SEARCH, --search SEARCH
                        search mac address in catalyst mac table
```

- analyze.py -d
- analyze.py -w
- analyze.py -c

この順で表示される情報量が増えていきます。


## Catalystでのパケットキャプチャ

Embedded Packet Capture機能を使うとCatalyst単独でパケットをキャプチャできます。

ただ、操作が面倒というか、どうやるのかすぐにわからなくなってしまうので、スクリプトにしておいた方が楽です。

```bash
(.venv) iida@s400win:~/git/home-network/bin$ ./capture_bootps.py --help
usage: capture_bootps.py [-h] [-t TESTBED] [-d DEVICE] [-bc] [-bu] [-ac] [-au] [--start] [--stop] [--export] [--get] [--status]

control embedded packet capture

optional arguments:
  -h, --help            show this help message and exit
  -t TESTBED, --testbed TESTBED
                        testbed YAML file
  -d DEVICE, --device DEVICE
                        device name
  -bc, --build_config   build config
  -bu, --build_unconfig
                        build unconfig
  -ac, --apply_config   apply config
  -au, --apply_unconfig
                        apply unconfig
  --start               start monitor
  --stop                start monitor
  --export              export to flash memory
  --get                 get pcap
  --status              retrieve monitor status
```

- capture_bootps.py --apply_config
- capture_bootps.py --start
- capture_bootps.py --stop
- capture_bootps.py --export
- capture_bootps.py --get

この順で実行します。

これはプロセススイッチされるbootpsメッセージだけを対象にキャプチャしますが、他の通信をキャプチャしたい場合はスクリプトのソースコードを書き換える必要があります。

マニュアルを確認しながら手作業でmonitorコマンドを打ち込むよりも、スクリプトに埋め込まれたパラメータを書き換えたほうが早いです。

<br><br>

# 機器の設定関連メモ

## Catalystの設定変更

MACアドレスの学習テーブルを定期的に採取するために、CatalystのMAC学習テーブルのエージングタイムを1時間に変更しています。

```bash
c2960cx-8pc(config)#mac address-table aging-time 3600
c2960cx-8pc(config)#end
```

## Netflow Liteの設定

Catalyst 2960CXはNetflow Liteを実装していますので、以下の設定を入れています。

```bash
!
flow record myrecord
 match ipv4 tos
 match ipv4 protocol
 match ipv4 source address
 match ipv4 destination address
 match ipv6 protocol
 match ipv6 source address
 match ipv6 destination address
 match transport source-port
 match transport destination-port
 collect transport tcp flags
 collect interface input
 collect flow sampler
 collect counter bytes long
 collect counter packets long
 collect timestamp sys-uptime first
 collect timestamp sys-uptime last
!
!
flow exporter myexporter
 destination 192.168.122.230
 source Vlan1
 transport udp 9996
 template data timeout 60
 option interface-table
 option exporter-stats
 option sampler-table
!
!
flow monitor mymonitor
 exporter myexporter
 cache timeout active 60
 statistics packet protocol
 record myrecord
!
!
sampler mysampler
 mode random 1 out-of 32
!
!
```

<br>

## Catalystの設定バックアップ

2台のCatalystでstartup-configを互いにコピーしあうことでバックアップします。
万が一壊れても対向装置側にコンフィグが残っていれば安心です。

この作業はpyATSを使って自動化しています。

- bin/backup_catalyst_config.py

```bash
(.venv) iida@s400win:~/git/home-network$ bin/backup_catalyst_config.py
usage: backup_catalyst_config.py [-h] [--testbed TESTBED] [-b]

backup catalyst startup-config

optional arguments:
  -h, --help         show this help message and exit
  --testbed TESTBED  testbed YAML file
  -b, --backup       backup startup-config each other
(.venv) iida@s400win:~/git/home-network$
```
