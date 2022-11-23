# LINE notify

LINEで通知する。

https://notify-bot.line.me/ja/


## 事前準備

1. LINEアプリでLINE Notifyを友だちに追加

    - 友だち検索で @linenotify を検索して出てきたものを追加

2. ブラウザでLINE Notifyのページにログイン

    - https://notify-bot.line.me/ja/

    - 画面右上の  ログイン  をクリック

    - メールアドレスとパスワードを入力してログイン

    - 画面に表示された認証番号をアプリのLINEに入力

    - ログインが完了すると画面右上が  ログイン  からアカウント名に切り替わる

3. アクセストークンを取得

    - 画面右上のアカウント名をクリック

    - マイページをクリック

    - アクセストークンの発行(開発者向け)が表示される

    - トークンを発行する  ボタンをクリック

    - トークン名は適当に付与　MyApp

    - トークルームは  1:1でLINE Notifyから通知を受け取る  を選択

    - 生成されたトークンを ~/.line_myapp にコピーペースト


## メッセージを送信

テキストメッセージなら簡単。

get_access_token()で~/.line_myappに記述したトークンを取得して、POSTするだけ。

```python

def send_line_notify(message: str, requests_options={}):

    URL = 'https://notify-api.line.me/api/notify'

    access_token = get_access_token()

    headers = {'Authorization': 'Bearer ' + access_token}

    payload = {'message': message}

    r = requests.post(URL, headers=headers, params=payload, **requests_options)

    r.raise_for_status()
```
