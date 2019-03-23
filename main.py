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
app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/list')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html'), 500


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


class Outline(object):

    def __init__(self):
        self.map_center=[35.284651, 139.555159]
        self.map_tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        self.attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'

    def run_bq_log(self, selects, table_name, devices, start_time, end_time, order_by_time=False):
        """Bigquery のテーブル をoutline_idでフィルターして取得"""
        # 練習ノート情報を取得
        # デバイスごとにログデータを取得
        client_bq = bigquery.Client()

        # クエリを作成
        select_str = ",".join(selects)
        devices_str = "'"+"','".join(devices)+"'"
        order_by_str = "ORDER BY loggingTime" if order_by_time else ""
        query_string = """
            SELECT
                {}
            FROM
                `{}`
            WHERE
                device_id IN ({})
                AND (TIMESTAMP_ADD(loggingTime, INTERVAL 9 HOUR) >= TIMESTAMP('{}')
                    AND TIMESTAMP_ADD(loggingTime, INTERVAL 9 HOUR) < TIMESTAMP('{}')
                )
            {}
            """.format(select_str, table_name, devices_str, start_time, end_time, order_by_str)
        print(query_string)

        query_job = client_bq.query(query_string)

        return query_job.result()

    def run_bq_html(self, table_name, outline_id):
        """
        Bigqueryにあるcloud storage上のhtmlファイル名テーブルをoutline_idでフィルターして取得
        """
        # 練習ノート情報を取得
        client_bq = bigquery.Client()

        # クエリを作成
        query_string = """
            SELECT
                outline_id
                ,html_name
            FROM
                `{}`
            WHERE
                outline_id = '{}'

            """.format(table_name, outline_id)
        print(query_string)

        query_job = client_bq.query(query_string)

        return query_job.result()

    def export_items_to_bigquery(self, dataset_id, tablename, rows_to_insert):
        """
        big queryにデータを挿入する
        :param dataset_id:
        :param tablename:
        :param rows_to_insert:
        :return:
        """
        # Instantiates a client
        bigquery_client = bigquery.Client()

        # Prepares a reference to the dataset
        dataset_ref = bigquery_client.dataset(dataset_id)

        table_ref = dataset_ref.table(tablename)
        table = bigquery_client.get_table(table_ref)  # API call

        errors = bigquery_client.insert_rows(table, rows_to_insert)  # API request
        print(errors)
        assert errors == []

    @app.route("/draw_map/<int:target_outline_id>", methods=['GET', 'POST'])
    def draw_map(target_outline_id):
        """
        航路マップを描画する（すでにある場合も再描画）
        :param target_outline_id:
        :param devices:
        :param colors:
        :return:
        """
        o = Outline()
        output_map_name = str(target_outline_id) + '.html'

        target_entities = query.get_outline_entities(target_outline_id)
        # エンティティ Noneは取り除く
        entities = [x for x in [e for e in list(target_entities[1]) if not dict(e).get('device_id') == '']
                    if dict(x).get("device_id") is not None]

        # デバイスID
        devices = [dict(e).get("device_id") for e in entities]

        # mapを描画
        my_map = folium.Map(o.map_center,
                            zoom_start=13,
                            tiles=o.map_tiles,
                            attr=o.attr)


        # 挺のカラーを取得
        colors = []
        for e in entities:
            yacht_no = dict(e).get("yacht_number")
            query_y = client.query(kind="Yacht")
            query_y.add_filter('yacht_no', '=', yacht_no)
            res = list(query_y.fetch())
            if len(res) < 1:
                colors.append("#000000")
            else:
                colors.append(dict(res[0]).get("color"))

        # デバイスごとにログを取得し、描画
        for i, d in enumerate(devices):
            sensor_logs = list(o.run_bq_log(selects=["locationLatitude", "locationLongitude"],
                                            table_name=os.environ.get('LOG_TABLE'), devices=[d],
                                            start_time=target_entities[0]["start_time"],
                                            end_time=target_entities[0]["end_time"],
                                            order_by_time=True))
            locations = [[dict(l).get("locationLatitude"), dict(l).get("locationLongitude")] for l in sensor_logs][::10]
            line = folium.PolyLine(locations=locations, color=colors[i], weight=1, opacity=0.5)
            my_map.add_child(line)

        # 一時ファイルに地図を出力
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            tmp_path = f.name
            my_map.save(tmp_path)

            # storageと接続
            blob = bucket.blob(output_map_name)
            blob.upload_from_filename(tmp_path, content_type="text/html")
            public_url = blob.public_url

        # bigqueryにhtmlファイルのURLを保存
        rows_to_insert = [[str(target_outline_id), public_url]]
        o.export_items_to_bigquery(dataset_id="smartphone_log",
                                   tablename="log_map",
                                   rows_to_insert=rows_to_insert)

        # 同じページにリダイレクト
        return redirect("/outline/" + str(target_outline_id))

    @app.route("/outline/<int:target_outline_id>", methods=['GET'])
    def outline_detail(target_outline_id):
        """練習概要ページを表示する"""
        o = Outline()

        # cloudstorageに保存するファイル名
        output_map_name = str(target_outline_id) + '.html'

        # query
        target_entities = query.get_outline_entities(target_outline_id)
        sorted_comments = query.get_user_comments(target_outline_id)
        outline_html = list(o.run_bq_html(table_name=os.environ.get('HTML_TABLE'),
                                     outline_id=target_outline_id))

        # エンティティ Noneは取り除く
        entities = [x for x in [e for e in list(target_entities[1]) if not dict(e).get('device_id') == '']
                    if dict(x).get("device_id") is not None]

        # デバイスID
        devices = [dict(e).get("device_id") for e in entities]

        # デバイスID
        yacht_number = [dict(e).get("yacht_number") for e in entities]

        # デバイスが登録されていなければ、GPSログなし、あれば、GPSログの数をカウント
        if len(entities) < 1:
            cnt_log = 0
            yacht_color = [["", ""]]
        else:
            # デバイスカラーを取得
            colors = []
            for e in entities:
                yacht_no = dict(e).get("yacht_number")
                query_y = client.query(kind="Yacht")
                query_y.add_filter('yacht_no', '=', yacht_no)
                res = list(query_y.fetch())
                if len(res) < 1:
                    colors.append("#000000")
                else:
                    colors.append(dict(res[0]).get("color"))

            # デバイスとカラー
            yacht_color = [{"yacht": y, "color": c} for y, c in zip(yacht_number, colors)]

            sensor_logs = list(o.run_bq_log(selects=["count(loggingTime) AS cnt"],
                                            table_name=os.environ.get('LOG_TABLE'),
                                            devices=devices,
                                            start_time=target_entities[0]["start_time"],
                                            end_time=target_entities[0]["end_time"],
                                            order_by_time=False))
            cnt_log = dict(sensor_logs[0]).get("cnt")

        # GPSログがなければ、なにもなし。GPSログがあれば地図に描画
        if cnt_log < 1:
            log_message = "GPSデータなし"
            public_url = ""
        else:
            log_message = "GPSデータあり"

            # storageに既にHTMLが生成されているか
            print(folium.TileLayer())
            if len(outline_html) < 1:
                log_message = "GPSデータマップ未作成"
                public_url = ""
            else:
                # storageからhtmlをダウンロード
                public_url = dict(outline_html[0]).get("html_name")

        return render_template('outline_detail.html', title='練習概要',
                                target_entities=target_entities,
                                sorted_comments=sorted_comments,
                               log_message=log_message,
                               html_url=public_url,
                               yacht_color=yacht_color)

    @app.route("/show_outline/<int:target_outline_id>/", methods=['GET','POST'])
    def show_outline(target_outline_id, is_new=None):
        """
        練習概要ページの内容を変更する画面に移動

        :arg
         target_outline_id:編集する練習ノートID
         is_new:新規作成かどうか（トップページからアクセスしたかどうか）
        """
        outline_selections = query.get_outline_selections()
        target_entities = query.get_outline_entities(target_outline_id)

        return render_template('show_outline.html', title='練習ノートを編集',\
                                target_entities=target_entities, outline_selections=outline_selections,
                               is_new=is_new)

    @app.route("/add_outline", methods=['POST', 'GET'])
    def add_outline(is_new=None):
        """TOPページから練習概要の日付、開始・終了時間、時間帯、IDを追加"""

        # 追加ボタンを押したタイミングで、outline IDを生成する
        outline_id = int(datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'))

        if datetime.now().hour <= 12:
            start_hour = 'T09:00'
            end_hour = 'T12:00'
        else:
            start_hour = 'T13:00'
            end_hour = 'T16:00'

        date = datetime.strftime(datetime.now(), '%Y-%m-%d')

        start_time = date + start_hour
        end_time = date + end_hour

        # 日付に対する曜日を取得
        day_tuple = ("(月)", "(火)", "(水)", "(木)", "(金)", "(土)", "(日)")
        day = day_tuple[datetime.now().weekday()]

        # DataStoreに格納
        key1 = client.key('Outline')
        outline1 = datastore.Entity(key1)
        outline1.update({
            'outline_id': outline_id,
            'date': date,
            'day': day,
            'start_time': start_time,
            'end_time': end_time,
            'icon_compass': "compass_null.png",
            'icon_flag': "flag_null.png",
            'icon_wave': "wave_null.png"
        })
        client.put(outline1)

        for new_entity in range(8):
            key2 = client.key('Outline_yacht_player')
            outline2 = datastore.Entity(key2)
            outline2.update({
                'outline_id': outline_id
            })
            client.put(outline2)

        outline_selections = query.get_outline_selections()
        target_entities = query.get_outline_entities(outline_id)

        return render_template('show_outline.html', title="新規ノート作成",
                               target_entities=target_entities, outline_selections=outline_selections, is_new=is_new)

    @app.route("/outline/mod_outline/<int:target_outline_id>", methods=['POST'])
    def mod_outline(target_outline_id):
        """練習概要ページのデータを修正・更新"""

        target_entities = query.get_outline_entities(target_outline_id)
        key_id_outline = target_entities[0].key.id
        key_outline = client.key('Outline', key_id_outline)
        outline = client.get(key_outline)

        # 日付、時間、風、波、練習メニューの値をshow_outline.htmlから取得
        date = request.form.get('date')
        start_time = request.form.get('start_time') + ":00" if len(request.form.get('start_time')) == 16 else request.form.get('start_time')
        end_time = request.form.get('end_time') + ":00" if len(request.form.get('end_time')) == 16 else request.form.get('end_time')
        wind_speedmin = request.form.get('windspeedmin')
        wind_speedmax = request.form.get('windspeedmax')
        wind_direction = request.form.get('winddirection')
        wind_speed_change = request.form.get('windspeedchange')
        sea_surface = request.form.get('seasurface')
        swell = request.form.get('swell')
        training1 = request.form.get('training1')
        training2 = request.form.get('training2')
        training3 = request.form.get('training3')
        training4 = request.form.get('training4')
        training5 = request.form.get('training5')
        training6 = request.form.get('training6')
        training7 = request.form.get('training7')
        training8 = request.form.get('training8')
        training9 = request.form.get('training9')
        training10 = request.form.get('training10')
        training11 = request.form.get('training11')
        training12 = request.form.get('training12')
        training13 = request.form.get('training13')
        training14 = request.form.get('training14')
        training15 = request.form.get('training15')

        day_tuple = ("(月)", "(火)", "(水)", "(木)", "(金)", "(土)", "(日)")
        day = day_tuple[datetime.strptime(date, '%Y-%m-%d').weekday()]

        #最大風速・風向・波に応じて、使用するアイコンを指定
        class_icon_selection = icon_selections.IconSelections()
        icon_flag = class_icon_selection.select_flag(wind_speedmax)
        icon_compass = class_icon_selection.select_compass(wind_direction)
        icon_wave = class_icon_selection.select_wave(sea_surface)

        # エンティティに値を入れる
        outline.update({
            'date': date,
            'day': day,
            'start_time': start_time,
            'end_time': end_time,
            'wind_speed_min': 0 if wind_speedmin == '' else int(wind_speedmin),
            'wind_speed_max': 0 if wind_speedmax == '' else int(wind_speedmax),
            'wind_direction': wind_direction,
            'wind_speed_change': wind_speed_change,
            'sea_surface': sea_surface,
            'swell': swell,
            'training1': training1,
            'training2': training2,
            'training3': training3,
            'training4': training4,
            'training5': training5,
            'training6': training6,
            'training7': training7,
            'training8': training8,
            'training9': training9,
            'training10': training10,
            'training11': training11,
            'training12': training12,
            'training13': training13,
            'training14': training14,
            'training15': training15,
            'icon_flag': icon_flag,
            'icon_wave': icon_wave,
            'icon_compass': icon_compass
        })

        client.put(outline)

        # show_outline.htmlから取得した値を変数に代入
        for i, yacht_entity in enumerate(target_entities[1]):
            yachtnumber = request.form.get('yachtnumber'+str(i))
            deviceid = request.form.get('deviceid'+str(i))
            skipper1 = request.form.get('skipper1'+str(i))
            skipper2 = request.form.get('skipper2'+str(i))
            skipper3 = request.form.get('skipper3'+str(i))
            crew1 = request.form.get('crew1'+str(i))
            crew2 = request.form.get('crew2'+str(i))
            crew3 = request.form.get('crew3'+str(i))

            # 艇番と選手の表を最適化する
            if skipper3:
                rowspan = 3
            elif skipper2:
                rowspan = 2
            else:
                rowspan = 1

            key_id_yacht = yacht_entity.key.id
            key_yacht = client.key('Outline_yacht_player', key_id_yacht)
            yacht = client.get(key_yacht)

            yacht.update({
                'yacht_number': yachtnumber,
                'device_id': deviceid,
                'skipper1': skipper1,
                'skipper2': skipper2,
                'skipper3': skipper3,
                'crew1': crew1,
                'crew2': crew2,
                'crew3': crew3,
                'rowspan': rowspan
                })

            client.put(yacht)

        return redirect(url_for('outline_detail', target_outline_id=target_outline_id))


    @app.route("/outline/del_outline/<int:target_outline_id>", methods=['POST'])
    def del_outline(target_outline_id):
        """練習概要ページの削除"""

        target_entities = query.get_outline_entities(target_outline_id)

        entity_id_1 = target_entities[0].key.id

        key1 = client.key('Outline', entity_id_1)
        client.delete(key1)

        for outline2 in target_entities[1]:
            entity_id_2 = outline2.key.id
            key2 = client.key('Outline_yacht_player', entity_id_2)
            client.delete(key2)

        return redirect(url_for('top'))


    @app.route("/outline/add_comment/<int:target_outline_id>", methods=['POST'])
    def add_comment(target_outline_id):
        """練習概要ページへのコメントの追加"""
        name = request.form.get('name')
        comment = request.form.get('comment')
        outline_id = int(target_outline_id)
        created_date = int(datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'))
        commented_date = datetime.strftime(datetime.now() + timedelta(hours=9), '%Y/%m/%d %H:%M')

        if name and comment and outline_id:
            key = client.key('Comment')
            user_comment = datastore.Entity(key)
            user_comment.update({
                'name': name,
                'comment': comment,
                'outline_id': outline_id,
                'created_date': created_date,
                'commented_date': commented_date
            })
            client.put(user_comment)

        return redirect(url_for('outline_detail', target_outline_id=target_outline_id))

    @app.route("/outline/showcomment/<int:comment_id>", methods=['GET'])
    def show_comment(comment_id):
        """コメントの編集・変更画面に移動"""

        key = client.key('Comment', comment_id)
        target_comment = client.get(key)

        return render_template('show_comment.html', target_comment=target_comment)


    @app.route("/outline/modcomment/<int:comment_id>", methods=['POST'])
    def mod_comment(comment_id):
        """ヨットデータの変更"""

        #HTML側で入力された内容の取得
        comment_name = request.form.get('comment-name')
        comment_text = request.form.get('comment-text')

        with client.transaction():
            key = client.key('Comment', comment_id)
            comment = client.get(key)

            if not comment:
                raise ValueError(
                    'Comment {} does not exist.'.format(comment_id))

            comment.update({
                'name': comment_name,
                'comment': comment_text
            })

            client.put(comment)

            target_outline_id = dict(comment).get("outline_id")

        return redirect(url_for('outline_detail', target_outline_id=target_outline_id))

    @app.route("/outline/delcomment/<int:comment_id>", methods=['POST'])
    def del_comment(comment_id):
        """ヨットデータの削除"""
        key = client.key('Comment', comment_id)

        #戻る練習概要のIDを取得
        comment = client.get(key)
        target_outline_id = dict(comment).get("outline_id")

        client.delete(key)

        return redirect(url_for('outline_detail', target_outline_id=target_outline_id))


class Player(object):
    """選手の管理に関するクラス"""

    @app.route("/admin/top")
    def admin_top():
        """
        管理ページのルートページ
        """
        return render_template('admin_top.html')

    @app.route("/admin/player")
    def admin_player():
        """選手の管理画面を表示"""

        query_p = client.query(kind='Player')
        players_list = list(query.fetch_retry(query_p))
        sorted_players = sorted(players_list, key=lambda player: player["admission_year"], reverse=True)


        #「入学年」の一覧を取得
        this_year = (datetime.now()).year
        admission_years = list(range(this_year-10, this_year+10))

        return render_template('admin_player.html', title='選手管理', \
        sorted_players=sorted_players, admission_years=admission_years)


    @app.route("/admin/addplayer", methods=['POST'])
    def add_player():
        """選手データの追加"""

        playername = str(request.form.get('playername'))
        year = request.form.get('year')
        datetime_now = datetime.now()

        if playername and year:
            key = client.key('Player')
            player = datastore.Entity(key)
            player.update({
                'player_name': playername,
                'admission_year': year,
                'created_date': datetime_now
            })
            client.put(player)

        return redirect(url_for('admin_player'))


    @app.route("/admin/showplayer/<int:player_id>", methods=['GET'])
    def show_player(player_id):
        """選手データの変更画面に移動"""

        key = client.key('Player', player_id)
        target_player = client.get(key)

        #入学年の一覧
        this_year = (datetime.now()).year
        admission_years = list(range(this_year-10, this_year+10))

        return render_template('show_player.html', title='ユーザー詳細',\
        target_player=target_player, admission_years=admission_years)


    @app.route("/admin/modplayer/<int:player_id>", methods=['POST'])
    def mod_player(player_id):
        """選手データの更新"""

        playername = str(request.form.get('playername'))
        year = request.form.get('year')

        with client.transaction():
            key = client.key('Player', player_id)
            player = client.get(key)

            if not player:
                raise ValueError(
                    'Player {} does not exist.'.format(player_id))

            player.update({
                'player_name' : str(playername),
                'admission_year' : year
            })

            client.put(player)

        return redirect(url_for('admin_player'))


    @app.route("/admin/delplayer/<int:player_id>", methods=['POST'])
    def del_player(player_id):
        """選手データの削除"""

        key = client.key('Player', player_id)
        client.delete(key)

        return redirect(url_for('admin_player'))


class Yacht(object):
    """ヨットの管理に関するクラス"""

    @app.route("/admin/yacht")
    def admin_yacht():
        """
        ヨットの管理画面の表示
        """
        query_y = client.query(kind='Yacht')
        yachts_list = list(query.fetch_retry(query_y))
        sorted_yachts = sorted(yachts_list, key=lambda yacht: yacht["yacht_no"])

        return render_template('admin_yacht.html', title = 'ヨット管理', sorted_yachts = sorted_yachts)

    @app.route("/admin/addyacht", methods=['POST'])
    def add_yacht():
        """ヨットデータの追加"""
        yachtno = request.form.get('yachtno')
        yachtclass = request.form.get('yachtclass')
        datetime_now = datetime.now()

        query_y = client.query(kind='Yacht')
        yacht_list = list(query.fetch_retry(query_y))

        colors = ["#45aaf2", "#eb3b5a", "#20bf6b","#3867d6", "#fa8231",
                  "#d1d8e0", "#fed330", "#0fb9b1", "#4b7bec","#778ca3"]
        color = colors[len(yacht_list) % 10]

        if yachtno and yachtclass:
            key = client.key('Yacht')
            yacht = datastore.Entity(key) #
            yacht.update({
                'yacht_no': yachtno,
                'yacht_class': yachtclass,
                'created_date': datetime_now,
                'color': color
            })
            client.put(yacht)

        return redirect(url_for('admin_yacht'))

    @app.route("/admin/showyacht/<int:yacht_id>", methods=['GET'])
    def show_yacht(yacht_id):
        """ヨットデータの変更画面に移動"""
        key = client.key('Yacht', yacht_id)
        target_yacht = client.get(key)

        return render_template('show_yacht.html', title='ユーザー詳細', target_yacht=target_yacht)

    @app.route("/admin/modyacht/<int:yacht_id>", methods=['POST'])
    def mod_yacht(yacht_id):
        """ヨットデータの変更"""
        yachtno = request.form.get('yachtno')
        yachtclass = request.form.get('yachtclass')

        with client.transaction():
            key = client.key('Yacht', yacht_id)
            yacht = client.get(key)

            if not yacht:
                raise ValueError(
                    'Yacht {} does not exist.'.format(yacht_id))
            yacht.update({
                'yacht_no': yachtno,
                'yacht_class': yachtclass
            })

            client.put(yacht)

        return redirect(url_for('admin_yacht'))

    @app.route("/admin/delyacht/<int:yacht_id>", methods=['POST'])
    def del_yacht(yacht_id):
        """ヨットデータの削除"""
        key = client.key('Yacht', yacht_id)
        client.delete(key)

        return redirect(url_for('admin_yacht'))


class Device(object):
    """デバイス管理に関するクラス"""

    @app.route("/admin/device")
    def admin_device():
        """デバイス管理画面の表示"""

        query_d = client.query(kind='Device')
        devices_list = list(query.fetch_retry(query_d))
        sorted_devices = sorted(devices_list, key=lambda device: device["device_id"])

        return render_template('admin_device.html', title='デバイス管理', sorted_devices=sorted_devices)

    @app.route("/admin/adddevice", methods=['POST'])
    def add_device():
        """デバイス情報を追加"""

        device_id = request.form.get('device_id')
        datetime_now = datetime.now()

        if device_id:
            key = client.key('Device')
            device = datastore.Entity(key)
            device.update({
                'device_id': device_id,
                'created_date': datetime_now
            })
            client.put(device)

        return redirect(url_for('admin_device'))

    @app.route("/admin/showdevice/<int:device_id>", methods=['GET'])
    def show_device(device_id):
        """デバイス情報の変更画面に移動"""

        key = client.key('Device', device_id)
        target_device = client.get(key)

        return render_template('show_device.html', title='デバイス詳細', target_device=target_device)

    @app.route("/admin/moddevice/<int:device_id>", methods=['POST'])
    def mod_device(device_id):
        """デバイス情報の変更"""

        deviceno = request.form.get('deviceno')
        devicename = request.form.get('devicename')

        with client.transaction():
            key = client.key('Device', device_id)
            device = client.get(key)

            if not device:
                raise ValueError(
                    'Device {} does not exist.'.format(device_id))

            device.update({
                'device_no': deviceno,
                'device_name': devicename
            })

            client.put(device)

        return redirect(url_for('admin_device'))

    @app.route("/admin/deldevice/<int:device_id>", methods=['POST'])
    def del_device(device_id):
        """デバイス情報の削除"""

        key = client.key('Device', device_id)
        client.delete(key)

        return redirect(url_for('admin_device'))


class Menu(object):
    @app.route("/admin/menu")
    def admin_menu():
        """練習メニューの管理画面を表示"""

        query_m = client.query(kind='Menu')
        menus_list = list(query.fetch_retry(query_m))
        sorted_menus = sorted(menus_list, key=lambda menu: menu["training_menu"])

        return render_template('admin_menu.html', title='練習メニュー', sorted_menus=sorted_menus)

    @app.route("/admin/addmenu", methods=['POST'])
    def add_menu():
        """練習メニューの追加"""

        menu_name = request.form.get('menu')

        if menu_name:
            key = client.key('Menu')
            menu = datastore.Entity(key)
            menu.update({
                'training_menu': menu_name
            })
            client.put(menu)

        return redirect(url_for('admin_menu'))

    @app.route("/admin/showmenu/<int:menu_id>", methods=['GET'])
    def show_menu(menu_id):
        """練習メニューの変更画面を表示"""

        key = client.key('Menu', menu_id)
        target_menu = client.get(key)

        return render_template('show_menu.html', title='練習メニュー詳細', target_menu=target_menu)

    @app.route("/admin/modmenu/<int:menu_id>", methods=['POST'])
    def mod_menu(menu_id):
        """練習メニューの変更"""

        menu_name = request.form.get('menu')

        with client.transaction():
            key = client.key('Menu', menu_id)
            menu = client.get(key)

            if not menu:
                raise ValueError(
                    'Menu {} does not exist.'.format(menu_id))

            menu.update({
                'training_menu': menu_name
            })

            client.put(menu)

        return redirect(url_for('admin_menu'))

    @app.route("/admin/delmenu/<int:menu_id>", methods=['POST'])
    def del_menu(menu_id):
        """練習メニューの削除"""

        key = client.key('Menu', menu_id)
        client.delete(key)

        return redirect(url_for('admin_menu'))


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
