from flask import Flask, render_template, request, redirect, url_for
from gcloud import datastore
from datetime import datetime, timedelta

# プロジェクトID
project_id = "web-yacht-note-208313"

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client(project_id)

# アプリケーションを作成
app = Flask(__name__)


@app.route('/')
def top():
    #
    # TOPページを表示したときの挙動
    #

    # 練習ノートの一覧を取得
    query = client.query(kind='Note')
    note_list = list(query.fetch())

    # 現在時刻を取得
    datetime_now = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M')

    return render_template('top.html', title='ユーザ一覧',
                           note_list=note_list, datetime_now = datetime_now)


@app.route("/add_note", methods=['POST'])
def add_note():
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')

    if starttime[0:10] == endtime[0:10]:
        notename = starttime[0:10] + "_" + starttime[11:13] + "-" + endtime[11:13]
    else:
        notename = starttime + endtime

    if starttime and endtime:
        key = client.key('Note') # kind（テーブル）を指定し、keyを設定
        note = datastore.Entity(key) # エンティティ（行）を指定のkeyで作成
        note.update({ # エンティティに入れるデータを指定
            'starttime': datetime.strptime(starttime, '%Y-%m-%dT%H:%M').astimezone(),
            'endtime': datetime.strptime(endtime, '%Y-%m-%dT%H:%M').astimezone(),
            'notename': notename
        })
        client.put(note) # DataStoreへ送信

    return redirect(url_for('top'))


@app.route("/note/<int:note_id>", methods=['GET'])
def show_note(note_id):
    key = client.key('Note', note_id)
    target_user = client.get(key)

    return render_template('show.html', title='ノート詳細', target_user=target_user)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
