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
from controllers.top import top_c
from controllers.log import log_c

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
app.register_blueprint(top_c)
app.register_blueprint(log_c)

@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/list')

# @app.route("/about")
# def about():
#     """WEBヨットノートを説明するページ"""
#     return render_template('about.html')


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

if __name__ == '__main__':
    app.run(host='0.0.0.0')
