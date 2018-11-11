from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from gcloud import datastore
from google.cloud import bigquery
from flask_bootstrap import Bootstrap
import numpy as np
import pandas as pd
from models import query

# プロジェクトID
project_id = "webyachtnote"

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client(project_id)

# アプリケーションを作成
app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.route('/', methods=['GET','POST'])
def top():
    """
    TOPページを表示したときの挙動
    """
    def get_form_value(form_name):
        form_value = request.form.get(form_name)
        if form_value in ['', '-']:
            form_value = None
        return form_value

    filters = ['filter_date', 'filter_time', 'filter_wind_speed',
                   'filter_wind_dir','filter_surface','filter_swell']

    # サイドバーからフィルターを使う場合のフォームから読み込み"
    form_values = {}
    for filter in filters:
        form_values[filter] = get_form_value(filter)

    # 練習ノートの一覧を取得
    query1 = client.query(kind='Outline')

    # フィルターの適用
    if form_values['filter_date'] is not None:
        query1.add_filter('date','=', form_values['filter_date'])

    if form_values['filter_time'] is not None:
        query1.add_filter('time_category','=', form_values['filter_time'])

    # if filter_wind_speed is not None:
    #     if filter_wind_speed == "軽風(0~3m/s)":
    #         query1.add_filter('wind_speed_min', '<=', 3)
    #     elif filter_wind_speed == "中風(4~7m/s)":
    #         query1.add_filter('wind_speed_max', '<=', )
    #
    #
    # if filter_wind_dir is not None:
    #     if filter_wind_dir == "北風":
    #         query1.add_filter('wind_speed_min','<', )
    #     elif filter_wind_dir == '南風'
    #         query1.add_filter('wind_speed_max', '>', 90)
    #         query1.add_filter('wind_speed_max', '<', 270)

    if form_values['filter_surface'] is not None:
        query1.add_filter('sea_surface','=', form_values['filter_surface'])

    if form_values['filter_swell'] is not None:
        query1.add_filter('swell','=', form_values['filter_swell'])

    # 各練習概要を表示
    outline_list = list(query1.fetch())

    #右サイドバーのフィルター用の項目
    outline_selections = query.get_outline_selections()

    return render_template('top.html', title='練習ノート一覧', outline_list=outline_list, \
                           outline_selections=outline_selections, form_default=form_values)

@app.route("/how_to_use")
def how_to_use():
    """
    使い方ページ
    """
    return render_template('how_to_use.html')


@app.route("/about")
def about():
    """
    WEBヨットノートを説明するページ
    """
    return render_template('about.html')


class Outline(object):

    @app.route("/outline/<int:target_outline_id>", methods=['GET'])
    def outline_detail(target_outline_id):
        """
        練習概要ページを表示する
        """

        target_entities = query.get_outline_entities(target_outline_id)
        user_comments = query.get_user_comments(target_outline_id)

        return render_template('outline_detail.html',title='練習概要',
                                target_entities=target_entities,
                                user_comments=user_comments)


    @app.route("/show_outline/<int:target_outline_id>/", methods=['GET','POST'])
    def show_outline(target_outline_id):
        """
        練習概要ページの内容を変更する画面に移動
        """

        outline_selections = query.get_outline_selections()
        target_entities = query.get_outline_entities(target_outline_id)

        return render_template('show_outline.html', title='練習概要変更',\
                                target_entities=target_entities, outline_selections=outline_selections)


    @app.route("/add_outline", methods=['POST'])
    def add_outline():
        """
        TOPページから練習概要の日付、開始・終了時間、時間帯、IDを追加
        """

        # フォームからデータを取得
        outline_id = int(datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'))

        #TOPから直接show_outline.htmlに接続する場合、不要
        # date = request.form.get('date')
        # time_category = request.form.get('time_category')
        # if time_category == "午前":
        #     start_time = "9:00"
        #     end_time = "12:30"
        # elif time_category == "午後":
        #     start_time = "13:30"
        #     end_time = "16:00"
        # elif time_category == "１部":
        #     start_time = "9:00"
        #     end_time = "11:30"
        # elif time_category == "２部":
        #     start_time = "11:30"
        #     end_time = "14:00"
        # else:
        #     start_time = "14:00"
        #     end_time = "16:30"

        # DataStoreに格納
        if outline_id:
            key1 = client.key('Outline')
            outline1 = datastore.Entity(key1)
            outline1.update({
                'outline_id': outline_id,
                # 'date': date,
                # 'time_category': time_category,
                # 'start_time': str(start_time),
                # 'end_time': str(end_time)
            })
            client.put(outline1)

            for new_entity in range(8):
                key2 = client.key('Outline_yacht_player')
                outline2 = datastore.Entity(key2)
                outline2.update({
                                'outline_id': outline_id
                })
                client.put(outline2)

        #TOPページで、入力せずに追加ボタンを押した場合は、TOPに戻る
        else:
            return redirect(url_for('top'))

        outline_selections = query.get_outline_selections()
        target_entities = query.get_outline_entities(outline_id)

        today = date.today()

        return render_template('show_outline.html', title="練習概要入力",today=today, \
                                target_entities=target_entities, outline_selections=outline_selections)


    @app.route("/outline/mod_outline/<int:target_outline_id>", methods=['POST'])
    def mod_outline(target_outline_id):
        """
        練習概要ページのデータを修正・更新
        """

        target_entities = query.get_outline_entities(target_outline_id)

        #日付、時間、風、波、練習メニューの値をshow_outline.htmlから取得
        date = request.form.get('date')
        time_category = request.form.get('timecategory')
        wind_speedmin = request.form.get('windspeedmin')
        wind_speedmax = request.form.get('windspeedmax')
        wind_direction_min = request.form.get('winddirectionmin')
        wind_direction_max = request.form.get('winddirectionmax')
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

        if time_category == "午前":
            start_time = "9:00"
            end_time = "12:30"
        elif time_category == "午後":
            start_time = "13:30"
            end_time = "16:00"
        elif time_category == "１部":
            start_time = "9:00"
            end_time = "11:30"
        elif time_category == "２部":
            start_time = "11:30"
            end_time = "14:00"
        else:
            start_time = "14:00"
            end_time = "16:30"

        if not target_entities[0]:
            raise ValueError(
                'Outline {} does not exist.'.format(outline1))

        target_entities[0].update({
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'time_category': time_category,
            'wind_speed_min': wind_speedmin,
            'wind_speed_max': wind_speedmax,
            'wind_direction_min': wind_direction_min,
            'wind_direction_max': wind_direction_max,
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
            'training15': training15
        })

        client.put(target_entities[0])

        #show_outline.htmlから取得した値を変数に代入
        for i,outline2 in enumerate(target_entities[1]):
            yachtnumber = request.form.get('yachtnumber'+str(i))
            deviceid = request.form.get('deviceid'+str(i))
            skipper1 = request.form.get('skipper1'+str(i))
            skipper2 = request.form.get('skipper2'+str(i))
            skipper3 = request.form.get('skipper3'+str(i))
            crew1 = request.form.get('crew1'+str(i))
            crew2 = request.form.get('crew2'+str(i))
            crew3 = request.form.get('crew3'+str(i))

            #艇番と選手の表を最適化する
            if skipper3:
                rowspan = 3
            elif skipper2:
                rowspan = 2
            else:
                rowspan = 1

            if not outline2:
                raise ValueError(
                    'Outline {} does not exist.'.format(outline2))

            outline2.update({
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

            client.put(outline2)

        return redirect(url_for('top'))


    @app.route("/outline/del_outline/<int:target_outline_id>", methods=['POST'])
    def del_outline(target_outline_id):
        """
        練習概要ページの削除

        Args:
        target_entities(list):
            インデックス0には、日時・波風・練習メニュー、インデックス1にはヨットとデバイス、部員のエンティティ
        entity_id_1(int): Outline kindのエンティティのID
        entity_id_2(int): Outline_yacht_player kindのエンティティのID

        Return:
        練習概要を削除し、TOPページに戻る
        """

        target_entities = query.get_outline_entities(target_outline_id)

        entity_id_1 = target_entities[0].key.id

        key1 = client.key('Outline', entity_id_1)
        client.delete(key1)

        for outline2 in target_entities[1]:
            entity_id_2 =  outline2.key.id
            key2 = client.key('Outline_yacht_player', entity_id_2)
            client.delete(key2)

        return redirect(url_for('top'))


    @app.route("/outline/add_comment/<int:target_outline_id>", methods=['POST'])
    def add_comment(target_outline_id):
        """
        練習概要ページへのコメントの追加

        Args:
        name: コメント者の名前
        comment: コメント

        Return:
        練習概要にコメントを追加し、再び練習概要ページに戻る
        """
        name = request.form.get('name') + ":"
        comment = request.form.get('comment')
        outline_id = int(target_outline_id)

        print(name)

        if name and comment and outline_id:
            key = client.key('Comment')
            user_comment = datastore.Entity(key)
            user_comment.update({
                'name': name,
                'comment': comment,
                'outline_id': outline_id
            })
            client.put(user_comment)

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
        """
        選手の管理画面を表示

        Args:
        player_list(list): 選手名と入学した年の一覧
        admission_years(list): ドラムロール表示用に、今年から+-10年の年の一覧

        Return: admin_player.htmlに移動。選手と年のリストを引き渡す
        """

        query = client.query(kind='Player')
        player_list = list(query.fetch())

        #「入学年」の一覧を取得
        this_year = (datetime.now()).year
        admission_years = list(range(this_year-10, this_year+10))

        return render_template('admin_player.html', title='選手管理', \
        player_list=player_list, admission_years=admission_years)


    @app.route("/admin/addplayer", methods=['POST'])
    def add_player():
        """
        選手データの追加

        Args:
        playername(str):admin_player.htmlで入力した選手名
        year(int):admin_player.htmlで入力した入学年
        datetime_now:データを作成した日時
        player: 新規で作成した、選手データのエンティティ。

        Return:
        TOPページに戻る
        """

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
        """
        選手データの変更画面に移動
        Args:
        target_player: 選手データのエンティティ
        admission_years: ドラムロール表示用の、今年+-10年の年の一覧

        Return:
        show_player.htmlに移動
        target_playerとadmission_yearsを引き渡す
        """

        key = client.key('Player', player_id)
        target_player = client.get(key)

        #入学年の一覧
        this_year = (datetime.now()).year
        admission_years = list(range(this_year-10, this_year+10))

        return render_template('show_player.html', title='ユーザー詳細',\
        target_player=target_player, admission_years=admission_years)


    @app.route("/admin/modplayer/<int:player_id>", methods=['POST'])
    def mod_player(player_id):
        """
        選手データの更新

        Args:
        playername(str): admin_player.htmlで選択した選手名
        year(int) :admin_player.htmlで選択した選手の入学年
        player: admin_player.htmlで選択した選手のエンティティ

        Return: TOPページに戻る
        """

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
        """
        選手データの削除
        Return: TOPページに戻る
        """

        key = client.key('Player', player_id)
        print(key)
        print(type(key))
        client.delete(key)

        return redirect(url_for('admin_player'))


class Yacht(object):
    """ヨットの管理に関するクラス"""

    @app.route("/admin/yacht")
    def admin_yacht():
        """
        ヨットの管理画面の表示

        Args:
        yacht_list(list):艇番と艇種を含んだエンティティのリスト

        Return: admin_yacht.htmlに移動。yacht_listを引き渡す。
        """
        query = client.query(kind='Yacht')
        yacht_list = list(query.fetch())

        return render_template('admin_yacht.html', title = 'ヨット管理', yacht_list = yacht_list)


    @app.route("/admin/addyacht", methods=['POST'])
    def add_yacht():
        """
        ヨットデータの追加

        Args:
        yachtno(int): 艇番
        yachtclass: 艇種
        datatime_now: データの作成日
        yacht: 新規作成したヨットのエンティティ

        return: TOPページに戻る
        """
        yachtno = request.form.get('yachtno')
        yachtclass = request.form.get('yachtclass')
        datetime_now = datetime.now()

        if yachtno and yachtclass:
            key = client.key('Yacht')
            yacht = datastore.Entity(key) #
            yacht.update({
                'yacht_no': yachtno,
                'yacht_class': yachtclass,
                'created_date': datetime_now
            })
            client.put(yacht)

        return redirect(url_for('admin_yacht'))


    @app.route("/admin/showyacht/<int:yacht_id>", methods=['GET'])
    def show_yacht(yacht_id):
        """
        ヨットデータの変更画面に移動

        Args:
        target_yacht: admin_yacht.htmlで選択したヨットデータ

        Return: show_yacht.htmlに移動。target_yachtを引き渡す。
        """

        key = client.key('Yacht', yacht_id)
        target_yacht = client.get(key)

        return render_template('show_yacht.html', title='ユーザー詳細', target_yacht=target_yacht)


    @app.route("/admin/modyacht/<int:yacht_id>", methods=['POST'])
    def mod_yacht(yacht_id):
        """
        ヨットデータの変更
        Args:
        yachtno: admin_yacht.htmlで入力された艇番
        yachtclass: admin_yacht.htmlで入力された艇種
        yacht: admin_yacht.htmlで選択したヨットのエンティティ

        Return: TOPページに戻る
        """

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
        """
        ヨットデータの削除

        Return: TOPページに戻る
        """

        key = client.key('Yacht', yacht_id)
        client.delete(key)

        return redirect(url_for('admin_yacht'))


class Device(object):
    """デバイス管理に関するクラス"""

    @app.route("/admin/device")
    def admin_device():
        """
        デバイス管理画面の表示

        Args:
        device_list(list): デバイスIDと機種名の一覧

        Return:
        admin_device.htmlに移動。device_listを引き渡す。
        """
        query = client.query(kind='Device')
        device_list = list(query.fetch())

        return render_template('admin_device.html', title='デバイス管理', device_list=device_list)


    @app.route("/admin/adddevice", methods=['POST'])
    def add_device():
        """
        デバイス情報を追加

        Args:
        deviceno: デバイスID
        decicename: デバイスの機種名
        datetime_now: 新規データの作成日時

        Return: TOPページに戻る
        """

        deviceno = request.form.get('deviceno')
        devicename = request.form.get('devicename')
        datetime_now = datetime.now()

        if deviceno and devicename:
            key = client.key('Device')
            device = datastore.Entity(key)
            device.update({
                'device_no': deviceno,
                'device_name': devicename,
                'created_date': datetime_now
            })
            client.put(device)

        return redirect(url_for('admin_device'))


    @app.route("/admin/showdevice/<int:device_id>", methods=['GET'])
    def show_device(device_id):
        """
        デバイス情報の変更画面に移動

        Args:
        target_device: admin_device.htmlで選択したデバイス情報

        Return:
        show_device.htmlに移動。target_deviceを引き渡す。
        """
        key = client.key('Device', device_id)
        target_device = client.get(key)

        return render_template('show_device.html', title='デバイス詳細', target_device=target_device)


    @app.route("/admin/moddevice/<int:device_id>", methods=['POST'])
    def mod_device(device_id):
        """
        デバイス情報の変更

        Args:
        deviceno: show_device.htmlで入力したデバイスID
        devicaname: show_device.htmlで入力した機種名
        device: show_device.htmlで選択したデバイス情報

        Return: TOPページに移動
        """
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
        """
        デバイス情報の削除

        Return:TOPページに戻る
        """
        key = client.key('Device', device_id)
        client.delete(key)

        return redirect(url_for('admin_device'))

class Menu(object):
    @app.route("/admin/menu")
    def admin_menu():
        """
        練習メニューの管理画面を表示

        Args:
        menu_list(list): 練習メニューの一覧

        Return:
        admin_menu.htmlに移動。menu_listを引き渡す。
        """

        query = client.query(kind='Menu')
        menu_list = list(query.fetch())
        return render_template('admin_menu.html', title='練習メニュー', menu_list=menu_list)

    @app.route("/admin/addmenu", methods=['POST'])
    def add_menu():
        """
        練習メニューの追加

        Args:
        menu_name: admin_menu.htmlから入力された練習メニュー

        Return:
        TOPページに戻る
        """
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
        """
        練習メニューの変更画面を表示

        Args:
        target_menu: admin_menu.htmlで選択した練習メニュー

        Return:
        show_menu.htmlに移動。target_menuを引き渡す
        """

        key = client.key('Menu', menu_id)
        target_menu = client.get(key)

        return render_template('show_menu.html', title='練習メニュー詳細', target_menu=target_menu)


    @app.route("/admin/modmenu/<int:menu_id>", methods=['POST'])
    def mod_menu(menu_id):
        """
        練習メニューの変更

        Args:
        menu_name: admin_menu.htmlで選択した練習メニュー
        menu: admin_menu.htmlで選択した練習メニューのエンティティ

        Return: TOPページに戻る
        """
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
        """
        練習メニューの削除

        Return: TOPページに戻る
        """

        key = client.key('Menu', menu_id)
        client.delete(key)

        return redirect(url_for('admin_menu'))


class Ranking(object):
    """ランキングクラス"""
    def query_by_outlineid(self,kind_name, target_outline_id):
        """
        Datastore のkind をoutline_idでフィルターして取得
        """
        # 練習ノート情報を取得
        query = client.query(kind=kind_name)
        query.add_filter('outline_id', '=', int(target_outline_id))
        result = query.fetch()

        return result

    def bq_query_by_deviceid(self,table_name, devices):
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
            """.format(table_name, devices_str)
        query_job = client_bq.query(query_string)
        # TODO 時間でフィルター

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
        haiteidata["haitei"] = haiteidata["yacht_number"] + "/" + \
                               haiteidata['skipper1'] + haiteidata['skipper2'] + haiteidata['skipper3'] + "/" \
                               + haiteidata['crew1'] + haiteidata['crew2'] + haiteidata['crew3']

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
        target_outline_id = '20181111125606'

        r = Ranking()

        # 対象
        outline = list(r.query_by_outlineid(kind_name="Outline",
                                            target_outline_id=target_outline_id))[0]
        outline_name = dict(outline).get('date') + dict(outline).get('time_category')

        # 配艇情報を取得
        haitei = list(r.query_by_outlineid(kind_name="Outline_yacht_player",
                                           target_outline_id=target_outline_id))

        # 対象の練習で使ったデバイス一覧
        devices = list(set([dict(h).get("device_id") for h in haitei if dict(h).get("device_id") is not None]))

        # 対象の練習時間のログを取得
        logs = list(r.bq_query_by_deviceid(table_name="webyachtnote.smartphone_log.sensorlog",
                                              devices=devices))

        # ログデータと配艇データをマージする
        merge_data = r.merge_logdata(sensorlog=logs, haitei=haitei)

        # メモリを節約するためいらない変数は削除
        del logs, haitei

        # 最高スピードを計算する
        max_speed_df = r.summarise_max_speed(merge_data)

        # 合計走行距離を計算する
        sum_distance_df = r.summarise_sum_distance(merge_data)

        # htmlにわたす用に、dict型に変換
        max_speed_values = dict()
        max_speed_values["speed"] = [round(x * 1.94384, 2) for x in max_speed_df["speed"].tolist()]
        max_speed_values["label"] = max_speed_df["haitei"].tolist()

        # htmlにわたす用に、dict型に変換
        sum_distance_values = dict()
        sum_distance_values["distance"] = sum_distance_df["distance"].tolist()
        sum_distance_values["label"] = sum_distance_df["haitei"].tolist()

        return render_template('ranking.html', title='ランキング',
                               outline_name=outline_name,
                               max_speed_values=max_speed_values,
                               sum_distance_values=sum_distance_values)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
