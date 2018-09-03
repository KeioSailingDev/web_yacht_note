from flask import Flask, render_template, request, redirect, url_for, flash
from gcloud import datastore
from datetime import datetime
from flask_bootstrap import Bootstrap

# プロジェクトID
project_id = "web-yacht-note-208313"

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client(project_id)

# アプリケーションを作成
app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.route('/')
def top():
    """
    TOPページを表示したときの挙動
    """
    # 練習ノートの一覧を取得
    query = client.query(kind='Note')
    note_list = list(query.fetch())

    # 現在時刻を取得
    datetime_now = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M')

    # 時間区分list
    time_categories = ["-","午前", "午後", "１部", "２部", "３部"]

    return render_template('top.html', title='ユーザ一覧',
                           note_list=note_list, datetime_now=datetime_now, time_categories=time_categories)


@app.route("/add_outline", methods=['POST'])
def add_outline():
    # フォームからデータを取得
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')
    time_category = request.form.get('time_category')

    # DataStoreに格納
    if starttime and endtime and time_category:
        key = client.key('Note') # kind（テーブル）を指定し、keyを設定
        outline = datastore.Entity(key) # エンティティ（行）を指定のkeyで作成
        outline.update({ # エンティティに入れるデータを指定
            'outline_id': datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'), # 日時をidとする
            'training_date': starttime[0:10],
            'starttime': datetime.strptime(starttime, '%Y-%m-%dT%H:%M').astimezone(),
            'endtime': datetime.strptime(endtime, '%Y-%m-%dT%H:%M').astimezone(),
            'time_category': time_category,
        })
        client.put(outline) # DataStoreへ送信
    else:
        return redirect(url_for('top'))

    # 元のページに戻る TODO 作成したページに移動に買える
    return redirect(url_for('top'))


@app.route("/note/<int:note_id>", methods=['GET'])
def show_note(note_id):
    key = client.key('Note', note_id)
    target_user = client.get(key)

    return render_template('show.html', title='ノート詳細', target_user=target_user)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
