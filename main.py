from datetime import datetime, timedelta
import os
import re
from flask import Flask, render_template, request, redirect, url_for, abort
import httplib2shim
httplib2shim.patch()
from google.cloud import datastore
from google.cloud import bigquery
from flask_bootstrap import Bootstrap
import pandas as pd
from models import query, icon_selections
from google.cloud import storage
import folium
import tempfile

# 分割先のコードをインポートする
from controllers.admin import admin_c
from controllers.outline import outline_c
from controllers.ranking import ranking_c
from controllers.how_to_use import how_to_use_c
from controllers.demand import demand_c

app = Flask(__name__)

# 環境変数を開発用と本番用で切り替え
os.environ['PROJECT_ID'] = 'webyachtnote'  #本番用
os.environ['LOG_TABLE'] = 'webyachtnote.smartphone_log.sensorlog'  #本番用
os.environ['HTML_TABLE'] = "webyachtnote.smartphone_log.log_map"  #本番用
os.environ['MAP_BUCKET'] = "gps_map"  #本番用
# os.environ['PROJECT_ID'] = 'web-yacht-note-208313'  # 開発用
# os.environ['LOG_TABLE'] = 'web-yacht-note-208313.smartphone_log.sensorlog'  # 開発用
# os.environ['HTML_TABLE'] = "web-yacht-note-208313.smartphone_log.log_map"  # 開発用
# os.environ['MAP_BUCKET'] = "gps_map_dev"  # 開発用

project_id = os.environ.get('PROJECT_ID')

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client()

# cloud storageのクライアント
storage_client = storage.Client()
bucket = storage_client.get_bucket(os.environ.get('MAP_BUCKET'))

# アプリケーションを作成
bootstrap = Bootstrap(app)

# 分割先のコントローラー(Blueprint)を登録する
app.register_blueprint(admin_c)
app.register_blueprint(outline_c)
app.register_blueprint(ranking_c)
app.register_blueprint(how_to_use_c)
app.register_blueprint(demand_c)


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/list')


@app.route('/list', methods=['GET', 'POST'])
def top():
    """
    TOPページを表示したときの挙動
    """
    def get_form_value(form_name):
        form_value = request.form.get(form_name)
        if form_value in ['', '-']:
            form_value = None
        return form_value

    filters = ['filter_date', 'filter_time', 'filter_wind_speed', 'filter_wind_dir','filter_wave']

    # サイドバーからフィルターを使う場合のフォームから読み込み"
    form_values = {}
    for filter in filters:
        form_values[filter] = get_form_value(filter)

    # 練習ノートの一覧を取得
    query1 = client.query(kind='Outline')


    # 各練習概要を表示（日付で降順に並び替え）
    outline_list = list(query.fetch_retry(query1, num=20))
    sorted_outline = sorted(outline_list, key=lambda outline: outline["date"], reverse=True)

    # 配艇情報をDataFrameにまとめる
    outline_df = pd.DataFrame({"outline_id": [dict(h).get('outline_id') for h in outline_list],
                               "date": [dict(h).get('date') for h in outline_list],
                               "day": [dict(h).get('day') for h in outline_list],
                               "time_category": [dict(h).get('time_category') for h in outline_list],
                               "icon_flag": [dict(h).get('icon_flag') for h in outline_list],
                               "icon_compass": [dict(h).get('icon_compass') for h in outline_list],
                               "icon_wave": [dict(h).get('icon_wave') for h in outline_list]})
    outline_df = outline_df.fillna("")

    # 日付
    if form_values['filter_date'] == "" or form_values['filter_date'] is not None:
        outline_df = outline_df[outline_df["date"].str.startswith(form_values['filter_date'])]

    # 風向
    if form_values["filter_wind_dir"] == "" or form_values['filter_wind_dir'] is not None:
        outline_df = outline_df[outline_df["icon_compass"].str.startswith(form_values['filter_wind_dir'])]

    # 風速
    if form_values["filter_wind_speed"] == "" or form_values['filter_wind_speed'] is not None:
        outline_df = outline_df[outline_df["icon_flag"].str.startswith(form_values['filter_wind_speed'])]

    # 波
    if form_values["filter_wave"] == "" or form_values['filter_wave'] is not None:
        outline_df = outline_df[outline_df["icon_wave"].str.startswith(form_values['filter_wave'])]

    # 並び替え
    outline_df = outline_df.sort_values(by="date", ascending=False)

    # １行ずつ辞書にしてリスト化
    outline_list = []
    for index, row in outline_df.iterrows():
        outline_list.append(dict(row))

    # 右サイドバーのフィルター用の項目
    outline_selections = query.get_outline_selections()

    return render_template('top.html', title='Webヨットノート', outline_list=outline_list,
                           outline_selections=outline_selections, form_default=form_values)





@app.route("/about")
def about():
    """WEBヨットノートを説明するページ"""
    return render_template('about.html')


#
# # error ====
# @app.route('/403')
# def abort403():
#     abort(403)
#
#
# @app.route('/404')
# def abort404():
#     abort(404)
#
#
# @app.route('/500')
# def abort500():
#     abort(500)
#
# @app.errorhandler(403)
# @app.errorhandler(404)
# @app.errorhandler(500)
# def error_handler(error):
#     print(error.code)
#     if error.code == 404:
#         error_message = "ページが存在しませんm(_ _)m"
#     elif error.code == 500:
#         error_message = "サーバーエラーが発生していますm(_ _)m。何度かページを更新すると改善することがあります。"
#     else:
#         error_message = "エラーが発生しました"
#     print(error_message)
#
#     return render_template("error_page.html", error_message=error_message)

# error ここまで====


class log_insert(object):
    @app.route("/log", methods=['POST'])
    def log_insert_bigquery(self):
        return 0


if __name__ == '__main__':
    app.run(host='0.0.0.0')
