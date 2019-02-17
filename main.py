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


@app.route("/how_to_use")
def how_to_use():
    """使い方ページ"""
    return render_template('how_to_use.html')


@app.route("/about")
def about():
    """WEBヨットノートを説明するページ"""
    return render_template('about.html')

@app.route("/demand")
def demand():
    """要望ページ"""
    # 練習ノートの一覧を取得
    query1 = client.query(kind='Demand')
    demands = list(query.fetch_retry(query1, num=20))
    # フィルター
    return render_template('demand.html', demands=demands)
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

class Ranking(object):
    """ランキングクラス"""

    def query_by_outlineid(self,kind_name, target_outline_id):
        """Datastore のkind をoutline_idでフィルターして取得"""

        # 練習ノート情報を取得
        _query = client.query(kind=kind_name)
        _query.add_filter('outline_id', '=', int(target_outline_id))
        result = query.fetch_retry(_query)

        return result

    def run_bq_query(self, table_name, devices, start_time, end_time):
        """
        Bigquery のテーブル をoutline_idでフィルターして取得
        """
        # 練習ノート情報を取得
        # デバイスごとにログデータを取得
        client_bq = bigquery.Client()

        # クエリを作成
        devices_str = "'"+"','".join(devices)+"'"
        query_string = """
            SELECT
                device_id
                ,speed
                ,distance
            FROM
                `{}`
            WHERE
                device_id IN ({})
                AND (TIMESTAMP_ADD(loggingTime, INTERVAL 9 HOUR) >= TIMESTAMP('{}')
                    AND TIMESTAMP_ADD(loggingTime, INTERVAL 9 HOUR) < TIMESTAMP('{}')
                )

            """.format(table_name, devices_str, start_time, end_time)
        print(query_string)

        query_job = client_bq.query(query_string)

        return query_job.result()

    def merge_logdata(self, sensorlog, haitei):
        """

        """
        # logをDataFrameにまとめる
        logdata = pd.DataFrame({"device": [dict(l).get("device_id") for l in sensorlog],
                                "speed": [dict(l).get('speed') for l in sensorlog],
                                "distance": [dict(l).get('distance') for l in sensorlog]})

        # 配艇情報をDataFrameにまとめる
        haiteidata = pd.DataFrame({"skipper1": [dict(h).get('skipper1') for h in haitei],
                                   "skipper2": [dict(h).get('skipper2') for h in haitei],
                                   "skipper3": [dict(h).get('skipper3') for h in haitei],
                                   "crew1": [dict(h).get('crew1') for h in haitei],
                                   "crew2": [dict(h).get('crew2') for h in haitei],
                                   "crew3": [dict(h).get('crew3') for h in haitei],
                                   "device": [dict(h).get("device_id") for h in haitei],
                                   "yacht_number": [dict(h).get("yacht_number") for h in haitei]})

        # 艇番＋乗艇者をまとめる
        haiteidata["haitei"] = [(y, re.sub("\s*$", "", str(s)), re.sub("\s*$", "", str(c))) for y, s, c in
                                zip(haiteidata["yacht_number"],
                                haiteidata['skipper1']+" "+haiteidata['skipper2']+" "+haiteidata['skipper3'],
                               haiteidata['crew1']+" "+haiteidata['crew2']+" "+haiteidata['crew3'])]

        # デバイス名で紐づけ
        return pd.merge(logdata, haiteidata, on='device')

    def summarise_max_speed(self, merged_data):
        """
        配艇ごとに、最高スピードを集計する

        :param merge_logdata:
        :return:
        """
        # 船ごとに集計
        max_speed_df = merged_data.groupby('haitei', as_index=False)["speed"].max()
        max_speed_df = max_speed_df.sort_values("speed", ascending=False)

        return max_speed_df

    def summarise_sum_distance(self, merged_data):
        """
        配艇ごとに、走行距離を集計する

        :param merge_logdata:
        :return:
        """
        print(merged_data)
        # 船ごとに集計
        sum_distance_df = merged_data.groupby('haitei', as_index=False)["distance"].sum()
        sum_distance_df = sum_distance_df.sort_values("distance", ascending=False)

        return sum_distance_df

    @app.route("/ranking", methods=['GET','POST'])
    def ranking():
        """
        ランキング画面の表示

        Args:
        Return:
        """
        r = Ranking()

        def get_form_value(form_name):
            form_value = request.form.get(form_name)
            if form_value in ['', '-']:
                form_value = None
            return form_value

        # 練習ノートの一覧を取得
        query1 = client.query(kind='Outline')
        outline_list = list(query.fetch_retry(query1))
        sorted_outlines = sorted(outline_list, key=lambda outline: outline["date"], reverse=True)

        target_outline_id = get_form_value("filter_outline")

        if target_outline_id is None:
            # デフォルトの表示ランキングを設定
            target_outline_id = sorted_outlines[0]["outline_id"]
        # 対象となるノート

        outline = [o for o in sorted_outlines if o["outline_id"] == int(target_outline_id)][0]
        time_category = dict(outline).get('time_category') if dict(outline).get('time_category') is not None else ""
        outline_name = dict(outline).get('date')+dict(outline).get('day')
        outline_id = dict(outline).get('outline_id')
        start_time = dict(outline).get('start_time')
        end_time = dict(outline).get('end_time')

        # 配艇情報を取得
        haitei = list(r.query_by_outlineid(kind_name="Outline_yacht_player",
                                           target_outline_id=target_outline_id))

        # 対象の練習で使ったデバイス一覧
        devices = list(set([dict(h).get("device_id") for h in haitei if dict(h).get("device_id") is not None]))

        # 対象の練習時間のログを取得
        logs = list(r.run_bq_query(table_name=os.environ.get('LOG_TABLE'),
                                              devices=devices, start_time=start_time, end_time=end_time))

        # ログデータと配艇データをマージする
        merge_data = r.merge_logdata(sensorlog=logs, haitei=haitei)

        # データがない場合のメッセージ
        no_value_message = "GPSデータがありません" if (len(merge_data) == 0) else  None

        # メモリを節約するためいらない変数は削除
        del logs, haitei

        # 最高スピードを計算する
        max_speed_df = r.summarise_max_speed(merge_data)

        # 合計走行距離を計算する
        sum_distance_df = r.summarise_sum_distance(merge_data)

        # htmlにわたす用に、dict型に変換
        max_speed_values = dict()
        max_speed_values["speed"] = [round(x * 1.94384, 1) for x in max_speed_df["speed"].tolist()]
        max_speed_values["label"] = max_speed_df["haitei"].tolist()

        # htmlにわたす用に、dict型に変換
        sum_distance_values = dict()
        sum_distance_values["distance"] = [round(d / 1000, 1) for d in sum_distance_df["distance"].tolist()] # km単位
        sum_distance_values["label"] = sum_distance_df["haitei"].tolist()

        # グラフの高さ（px）
        canvas_height = len(max_speed_df) * 100

        return render_template('ranking.html', title='ランキング',
                               no_value_message=no_value_message,
                               outline_name=outline_name,
                               outline_id=outline_id,
                               target_outline_id=target_outline_id,
                               max_speed_values=max_speed_values,
                               sum_distance_values=sum_distance_values,
                               sorted_outlines=sorted_outlines,
                               canvas_height=canvas_height)

class log_insert(object):
    @app.route("/log", methods=['POST'])
    def log_insert_bigquery(self):
        return 0


if __name__ == '__main__':
    app.run(host='0.0.0.0')
