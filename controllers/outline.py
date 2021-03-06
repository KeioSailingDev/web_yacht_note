#標準
from datetime import datetime, timedelta
import os
import re

#外部
from flask import Flask, render_template, request, redirect, url_for, abort, Blueprint
import httplib2shim
httplib2shim.patch()
from google.cloud import bigquery
from flask_bootstrap import Bootstrap
import folium
import tempfile
import pandas as pd
from google.cloud import datastore
from google.cloud import storage

#他スクリプト
from controllers import query, icon

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client()

# cloud storageのクライアント
storage_client = storage.Client()
bucket = storage_client.get_bucket("gps_map")

# "outline_c"という名前でBlueprintオブジェクトを生成します
outline_c = Blueprint('outline_c', __name__)

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

        query_job = client_bq.query(query_string)

        return query_job.result()

    def run_map_query(self, outline_id):
        """
        htmlmapファイル名テーブルをoutline_idでフィルターして取得
        """
        query = client.query(kind='Map')
        query.add_filter('outline_id', '=', str(outline_id))

        return list(query.fetch())

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
        assert errors == []

    @outline_c.route("/draw_map/<int:target_outline_id>", methods=['GET', 'POST'])
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
                            attr="-")


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
        key = client.key('Map')
        map_ent = datastore.Entity(key)
        map_ent.update({
                'outline_id': str(target_outline_id),
                'html_url': public_url
        })
        client.put(map_ent)

        # 同じページにリダイレクト
        return redirect("/outline/" + str(target_outline_id))

    @outline_c.route("/outline/<int:target_outline_id>", methods=['GET'])
    def outline_detail(target_outline_id):
        """練習概要ページを表示する"""

        o = Outline()

        # cloudstorageに保存するファイル名
        output_map_name = str(target_outline_id) + '.html'

        # query
        target_entities = query.get_outline_entities(target_outline_id)
        # print("エンティティ")
        # print(target_entities)

        sorted_comments = query.get_user_comments(target_outline_id)
        outline_html = list(o.run_map_query(outline_id=target_outline_id))

        # 配艇エンティティ ※Noneは取り除く
        entities = [x for x in [e for e in list(target_entities[1]) if not dict(e).get('device_id') == '']
                    if dict(x).get("device_id") is not None]
        # デバイスID
        devices = [dict(e).get("device_id") for e in entities]

        # デバイスID
        yacht_number = [dict(e).get("yacht_number") for e in entities]

        # init
        yacht_color = [["", ""]]
        log_message = "GPSデータなし"
        public_url = ""

        #ページタイトル
        page_title = target_entities[0]['date'] + target_entities[0]['day']

        # デバイスが登録されていなければ、GPSログなし、あれば、GPSログの数をカウント
        if len(entities) < 1:
            pass
        else:
            if len(outline_html) < 1:
                sensor_logs = list(o.run_bq_log(selects=["count(loggingTime) AS cnt"],
                                                table_name=os.environ.get('LOG_TABLE'),
                                                devices=devices,
                                                start_time=target_entities[0]["start_time"],
                                                end_time=target_entities[0]["end_time"],
                                                order_by_time=False))
                cnt_log = dict(sensor_logs[0]).get("cnt")
                if cnt_log < 1:
                    pass
                else:
                    log_message = "GPSデータあり"

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
                    yacht_color = [{"yacht": y, "color": c} for y, c in zip(yacht_number, colors)]
            else:
                log_message = "GPSデータあり"
                # storageからhtmlをダウンロード
                public_url = dict(outline_html[0]).get("html_url")

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
                yacht_color = [{"yacht": y, "color": c} for y, c in zip(yacht_number, colors)]

    ###練習メニューの円グラフ化###
        #円グラフ用のデータを設定 →　pandasで、ダブった練習メニューを合算し、割合に変換する
        training_data = pd.DataFrame({"training_menu":[dict(target_entities[0]).get("training"+str(i)) for i in range(1,16)],
                                      "training_time":[dict(target_entities[0]).get("training_time"+str(i)) for i in range(1,16)]})
        #カラム"training_menu"が空の者は削除
        training_data.drop(training_data.index[training_data.training_menu == ''], inplace=True)

        #同じ練習メニューのものは合算する
        training_data = training_data.groupby('training_menu', as_index=False)["training_time"].sum()
        training_data = training_data.sort_values(by="training_time", ascending=False)

        # 出力をまとめる
        data_dict=dict()
        data_dict["training_menu"] = training_data["training_menu"].tolist()
        data_dict["training_time"] = training_data["training_time"].tolist()
        data_dict["training_ratio"] = training_data['training_time'].apply(lambda x: round((x/training_data['training_time'].sum())*100)).tolist()

        return render_template('outline_detail.html', title='練習概要',
                                page_title=page_title,
                                target_entities=target_entities,
                                sorted_comments=sorted_comments,
                                log_message=log_message,
                                html_url=public_url,
                                yacht_color=yacht_color,
                                training_data=data_dict)

    @outline_c.route("/gps_animation/<int:target_outline_id>/", methods=['GET','POST'])
    def gps_animation(target_outline_id, is_new=None):

        target_entities = query.get_outline_entities(target_outline_id)
        page_title = target_entities[0]['date'] + target_entities[0]['day']

        return render_template('gps_animation.html', page_title=page_title)


    @outline_c.route("/show_outline/<int:target_outline_id>/", methods=['GET','POST'])
    def show_outline(target_outline_id, is_new=None):
        """
        練習概要ページの内容を変更する画面に移動

        :arg
         target_outline_id:編集する練習ノートID
         is_new:新規作成かどうか（トップページからアクセスしたかどうか）
        """

        #新規ノートを作成する場合、初めに仮のエンティティを生成する　→　ノート作成ボタンを押して初めて作成
        if target_outline_id == 0:

            ###①仮の基本情報###
            #追加ボタンを押したタイミングで、outline IDを生成する
            outline_id = 0

            #作成日
            date = datetime.strftime(datetime.now(), '%Y-%m-%d')

            #日付に対する曜日を取得
            day_tuple = ("(月)", "(火)", "(水)", "(木)", "(金)", "(土)", "(日)")
            day = day_tuple[datetime.now().weekday()]

            #練習の開始・終了時間を入力
            start_hour = 'T09:00'
            end_hour = 'T16:00'
            start_time = date + start_hour
            end_time = date + end_hour

            provisional_entity1 = {}

            provisional_entity1.update({
                'outline_id': outline_id,
                'date': date,
                'day': day,
                'start_time': start_time,
                'end_time': end_time
            })

            ###②仮の配艇情報###
            provisional_entity2 = []

            for provisional_yacht in range(8):
                provisional_yacht = {}
                provisional_yacht['outline_id'] = outline_id
                provisional_entity2.append(provisional_yacht)

            #①と②を統合、新規ノートと識別するために、文字列「new_note」を付与
            target_entities = [provisional_entity1, provisional_entity2]

        else:
            target_entities = query.get_outline_entities(target_outline_id)

        outline_selections = query.get_outline_selections()

        return render_template('show_outline.html', title='練習ノートを編集', page_title='練習ノートを編集',\
                                target_entities=target_entities, outline_selections=outline_selections)

    @outline_c.route("/outline/mod_outline/<int:target_outline_id>", methods=['POST'])
    def mod_outline(target_outline_id):

        if target_outline_id == 0:
            outline_id = int(datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'))

            key1 = client.key('Outline')
            outline1 = datastore.Entity(key1)
            outline1.update({'outline_id': outline_id})
            client.put(outline1)

            for new_entity in range(8):
                key2 = client.key('Outline_yacht_player')
                outline2 = datastore.Entity(key2)
                outline2.update({'outline_id': outline_id})
                client.put(outline2)

                target_outline_id = outline_id

        target_entities = query.get_outline_entities(target_outline_id)
        key_id_outline = target_entities[0].key.id
        key_outline = client.key('Outline', key_id_outline)
        outline = client.get(key_outline)

        #show_outline.htmlで入力された情報を取得
        date = request.form.get('date')
        start_time = request.form.get('start_time') + ":00" if len(request.form.get('start_time')) == 16 else request.form.get('start_time')
        end_time = request.form.get('end_time') + ":00" if len(request.form.get('end_time')) == 16 else request.form.get('end_time')
        wind_speedmin = request.form.get('windspeedmin')
        wind_speedmax = request.form.get('windspeedmax')

        wind_direction = request.form.get('winddirection')
        if wind_direction is None:
            wind_direction = "未入力"

        wind_speed_change = request.form.get('windspeedchange')
        if wind_speed_change is None:
            wind_speed_change = "未入力"

        wind_direction_change = request.form.get('winddirectionchange')
        if wind_direction_change is None:
            wind_speed_change = "未入力"

        sea_surface = request.form.get('seasurface')
        if sea_surface is None:
            sea_surface = "未入力"

        swell = request.form.get('swell')
        if swell is None:
            swell = "未入力"

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
        training_time1 = int(request.form.get('training_time1'))
        training_time2 = int(request.form.get('training_time2'))
        training_time3 = int(request.form.get('training_time3'))
        training_time4 = int(request.form.get('training_time4'))
        training_time5 = int(request.form.get('training_time5'))
        training_time6 = int(request.form.get('training_time6'))
        training_time7 = int(request.form.get('training_time7'))
        training_time8 = int(request.form.get('training_time8'))
        training_time9 = int(request.form.get('training_time9'))
        training_time10 = int(request.form.get('training_time10'))
        training_time11 = int(request.form.get('training_time11'))
        training_time12 = int(request.form.get('training_time12'))
        training_time13 = int(request.form.get('training_time13'))
        training_time14 = int(request.form.get('training_time14'))
        training_time15 = int(request.form.get('training_time15'))

        #曜日の取得
        day_tuple = ("(月)", "(火)", "(水)", "(木)", "(金)", "(土)", "(日)")
        day = day_tuple[datetime.strptime(date, '%Y-%m-%d').weekday()]

        #最大風速・風向・波に応じて、使用するアイコンを指定
        class_icon_selection = icon.IconSelections()
        icon_flag = class_icon_selection.select_flag(wind_speedmax)
        icon_compass = class_icon_selection.select_compass(wind_direction)
        icon_wave = class_icon_selection.select_wave(sea_surface)

        #エンティティに入力した情報を格納する
        outline.update({
            'date': date,
            'day': day,
            'start_time': start_time,
            'end_time': end_time,
            'wind_speed_min': 0 if wind_speedmin == '' else int(wind_speedmin),
            'wind_speed_max': 0 if wind_speedmax == '' else int(wind_speedmax),
            'wind_direction': wind_direction,
            'wind_speed_change': wind_speed_change,
            'wind_direction_change': wind_direction_change,
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
            'training_time1': training_time1,
            'training_time2': training_time2,
            'training_time3': training_time3,
            'training_time4': training_time4,
            'training_time5': training_time5,
            'training_time6': training_time6,
            'training_time7': training_time7,
            'training_time8': training_time8,
            'training_time9': training_time9,
            'training_time10': training_time10,
            'training_time11': training_time11,
            'training_time12': training_time12,
            'training_time13': training_time13,
            'training_time14': training_time14,
            'training_time15': training_time15,
            'icon_flag': icon_flag,
            'icon_wave': icon_wave,
            'icon_compass': icon_compass
        })

        client.put(outline)

      ####配艇エンティティの編集###
        for i, yacht_entity in enumerate(target_entities[1]):
            key_id_yacht = yacht_entity.key.id
            key_yacht = client.key('Outline_yacht_player', key_id_yacht)
            yacht = client.get(key_yacht)

            #show_outline.htmlで入力された情報を取得
            yachtnumber = request.form.get('yachtnumber'+str(i))
            deviceid = request.form.get('deviceid'+str(i))
            skipper1 = request.form.get('skipper1'+str(i))
            skipper2 = request.form.get('skipper2'+str(i))
            skipper3 = request.form.get('skipper3'+str(i))
            skipper4 = request.form.get('skipper4'+str(i))
            crew1 = request.form.get('crew1'+str(i))
            crew2 = request.form.get('crew2'+str(i))
            crew3 = request.form.get('crew3'+str(i))
            crew4 = request.form.get('crew4'+str(i))

            # 艇番と選手の表を最適化する
            if skipper4:
                rowspan = 4
            elif skipper3:
                rowspan = 3
            elif skipper2:
                rowspan = 2
            else:
                rowspan = 1

            #エンティティに入力した情報を格納する
            yacht.update({
                'yacht_number': yachtnumber,
                'device_id': deviceid,
                'skipper1': skipper1,
                'skipper2': skipper2,
                'skipper3': skipper3,
                'skipper4': skipper4,
                'crew1': crew1,
                'crew2': crew2,
                'crew3': crew3,
                'crew4': crew4,
                'rowspan': rowspan
                })

            client.put(yacht)

        return redirect(url_for('outline_c.outline_detail',target_outline_id=target_outline_id))

    @outline_c.route("/outline/del_outline/<int:target_outline_id>", methods=['POST'])
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

        return redirect(url_for('top_c.top'))


    @outline_c.route("/outline/add_comment/<int:target_outline_id>", methods=['POST'])
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

        return redirect(url_for('outline_c.outline_detail', target_outline_id=target_outline_id))

    @outline_c.route("/outline/showcomment/<int:comment_id>", methods=['GET'])
    def show_comment(comment_id):
        """コメントの編集・変更画面に移動"""

        key = client.key('Comment', comment_id)
        target_comment = client.get(key)

        return render_template('show_comment.html', target_comment=target_comment)


    @outline_c.route("/outline/modcomment/<int:comment_id>", methods=['POST'])
    def mod_comment(comment_id):
        """コメントの変更"""

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

        return redirect(url_for('outline_c.outline_detail', target_outline_id=target_outline_id))

    @outline_c.route("/outline/delcomment/<int:comment_id>", methods=['POST'])
    def del_comment(comment_id):
        """コメントの削除"""
        key = client.key('Comment', comment_id)

        #戻る練習概要のIDを取得
        comment = client.get(key)
        target_outline_id = dict(comment).get("outline_id")

        client.delete(key)

        return redirect(url_for('outline_c.outline_detail', target_outline_id=target_outline_id))

    @outline_c.route("/outline/post_slack/<int:target_outline_id>", methods=['GET'])
    def post_slack(target_outline_id):
        """slackに投稿する"""
        # 情報を取得
        o = Outline()
        # cloudstorageに保存するファイル名
        output_map_name = str(target_outline_id) + '.html'

        # query
        target_entities = query.get_outline_entities(target_outline_id)
        sorted_comments = query.get_user_comments(target_outline_id)
        outline_html = list(o.run_map_query(outline_id=target_outline_id))

        import slackweb

        # 投稿文の整形
        slack_text = target_entities[0]["date"] + target_entities[0]["day"]
        slack_channel="post_test"
        attachments=[]
        condition={
                    "color": "#36a64f",
                    "fields":[
                        {
                        "title": "風向風速",
                        "value": target_entities[0]["wind_direction"]+" " +
                        str(target_entities[0]["wind_speed_min"])+"m/s ~ "
                        +str(target_entities[0]["wind_speed_max"])+"m/s",
                        "short": False
                        },
                        {
                        "title": "風速変化量",
                        "value": target_entities[0]["wind_speed_change"],
                        "short": False
                        },
                        {
                        "title": "風向変化量",
                        "value": target_entities[0]["wind_direction_change"],
                        "short": False
                        },
                        {
                        "title": "波",
                        "value": target_entities[0]["sea_surface"],
                        "short": False
                        },
                        {
                        "title": "うねり",
                        "value": target_entities[0]["swell"],
                        "short": False
                        },
                    ]
                }

        training={
                    "color": "#ff3300",
                    "fields":[
                        {
                        "title": "練習メニュー",
                        "value": "\n".join([target_entities[0]["training"+str(i)] for i in range(1,16)]),
                        "short": False
                        },
                    ]
                }

        yacht={
                    "color": "#3300cc",
                    "fields":[
                        {
                        "title": "練習艇",
                        "value": " ".join([str(x["yacht_number"]) for x in target_entities[1]]),
                        "short": False
                        },
                    ]
                }
        comments={
                    "color": "#cccccc",
                    "fields":[
                        {
                        "title": comment["name"],
                        "value": comment["comment"],
                        "short": False
                        }
                    for comment in sorted_comments
                    ]
        }
        link={
            "title": "Webヨットノートで開く",
            "title_link": "https://webyachtnote.appspot.com/outline/"+str(target_outline_id)
        }

        attachments.append(condition)
        attachments.append(training)
        attachments.append(yacht)
        attachments.append(comments)
        attachments.append(link)

        # 投稿
        slack = slackweb.Slack(url="https://hooks.slack.com/services/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")
        slack.notify(text=slack_text, channel=slack_channel, attachments=attachments)
        return redirect("/outline/" + str(target_outline_id))
