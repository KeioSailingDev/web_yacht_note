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
    query = client.query(kind='Outline')
    outline_list = list(query.fetch())

    # 現在時刻を取得
    datetime_now = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M')

    # 時間区分list
    time_categories = ["-", "午前", "午後", "１部", "２部", "３部"]

    return render_template('top.html', title='練習ノート一覧',
                           outline_list=outline_list, datetime_now=datetime_now, time_categories=time_categories)


@app.route("/add_outline", methods=['POST'])
def add_outline():
    # フォームからデータを取得
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')
    time_category = request.form.get('time_category')

    # DataStoreに格納
    if starttime and endtime and time_category:
        key = client.key('Outline')  # kind（テーブル）を指定し、keyを設定
        outline = datastore.Entity(key)  # エンティティ（行）を指定のkeyで作成
        outline.update({  # エンティティに入れるデータを指定
            'outline_id': datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'),  # 日時をidとする
            'training_date': starttime[0:10],
            'starttime': datetime.strptime(starttime, '%Y-%m-%dT%H:%M').astimezone(),
            'endtime': datetime.strptime(endtime, '%Y-%m-%dT%H:%M').astimezone(),
            'time_category': time_category,
        })
        client.put(outline)  # DataStoreへ送信
    else:
        return redirect(url_for('top'))

    # 元のページに戻る TODO 作成したページに移動に買える
    return redirect(url_for('top'))


# 【練習概要のページを表示】2種類のOutline Kindのデータを持ってくる
@app.route("/outline/<int:target_outline_id>", methods=['GET'])
def outline_detail(target_outline_id):
    # 日付,時間帯、波、風、練習メニューのデータを取得
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', target_outline_id)
    target_outline1 = list(query1.fetch())[0]  # 該当エンティティは一つしかないため、[0]で一つ目を指定
    # outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    # 取得したエンティティを変数に代入し、htmlファイルに渡す

    # 艇番、スキッパー、クルーのデータを取得
    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', target_outline_id)
    target_outline2 = list(query2.fetch())
    # outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    # 取得したエンティティを変数に代入し、htmlファイルに渡す
    # Outline_yacht_player Kindからは複数のエンティティを取得する為、listにしてデータを取得する

    return render_template('outline_detail.html', title='練習概要', target_outline1=target_outline1,
                           target_outline2=target_outline2)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
