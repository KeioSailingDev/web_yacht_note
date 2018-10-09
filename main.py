from flask import Flask, render_template, request, redirect, url_for
from gcloud import datastore
from datetime import datetime
from flask_bootstrap import Bootstrap
from datetime import date

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

    # 本日の日付を取得
    today = date.today()

    # 時間区分list
    time_categories = ["-", "午前", "午後", "１部", "２部", "３部"]

    return render_template('top.html', title='練習ノート一覧',outline_list=outline_list,
                           today=today, time_categories=time_categories)

                           
@app.route("/outline/<int:target_outline_id>", methods=['GET'])
def outline_detail(target_outline_id):
    """
    練習概要ページを表示する

    Args:
    target_outline1: 日付、時間帯、波、風、練習メニューを含んだエンティティ
    target_outline2(list): 艇番、スキッパー、クルーを含んだエンティティ。

    Return:
    outline_detail.htmlへ移動し、target_outline1、target_outline2のデータを表示
    """
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', int(target_outline_id))#outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    target_outline1 = list(query1.fetch())[0]#該当するエンティティは一つしかないため、[0]で一つ目を指定

    #艇番、スキッパー、クルーのデータを取得
    query2 = client.query(kind='Outline_yacht_player')#outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    query2.add_filter('outline_id', '=', int(target_outline_id))
    target_outline2 = list(query2.fetch())

    return render_template('outline_detail.html',\
     title='練習概要', target_outline1=target_outline1, target_outline2=target_outline2)


@app.route("/admin/show_outline/<int:target_outline_id>/", methods=['GET'])
def show_outline(target_outline_id):
    """
    練習概要ページの内容を変更する画面に移動

    Args:
    target_outline1: 日付、時間帯、波、風、練習メニューを含んだエンティティ
    target_outline2(list): 艇番、スキッパー、クルーを含んだエンティティ。
    time_categories, wind_speeds, wind_directions, sizes, sea_surfaces,
    yacht_numbers, device_names, player_names, training_menus: ドラムロールで表示する内容の変数

    Return:
    show_outline.htmlに移動し、target_outline1、target_outline2を表示
    """

    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', int(target_outline_id))
    target_outline1 = list(query1.fetch())[0]


    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', int(target_outline_id))
    target_outline2 = list(query2.fetch())

    #時間区分の一覧
    time_categories = ("-", "午前", "午後", "１部", "２部", "３部")

    #風速の値一覧
    wind_speeds = range(0,21)

    #風向の値一覧
    wind_directions = range(0, 360)

    #うねりと風速変化の項目
    sizes = ("-", "小", "中", "大")

    #海面の項目一覧
    sea_surfaces = ("-", "フラット", "チョッピー", "高波")

    #ドラムロール表示用に、艇番の一覧を取得
    query_yacht = client.query(kind='Yacht')
    yacht_numbers = list(query_yacht.fetch())

    #デバイス機種名の一覧を取得
    query_device = client.query(kind='Device')
    device_names = list(query_device.fetch())

    #ドラムロール表示用に、部員の一覧を取得
    query_player = client.query(kind='Player')
    player_names = list(query_player.fetch())

    #ドラムロール表示用に、練習メニューの一覧を取得
    query_menu = client.query(kind='Menu')
    training_menus = list(query_menu.fetch())

    return render_template('show_outline.html', title='練習概要変更',\
                            target_outline1=target_outline1, target_outline2=target_outline2,\
                            wind_speeds=wind_speeds, wind_directions=wind_directions,\
                            time_categories=time_categories, sizes=sizes, sea_surfaces=sea_surfaces,\
                            training_menus=training_menus, yacht_numbers=yacht_numbers,\
                            player_names=player_names, device_names=device_names)
                           

@app.route("/add_outline", methods=['POST'])
def add_outline():
    """
    TOPページから練習概要の日付、開始・終了時間、時間帯、IDを追加

    Args:

    Return:

    """

    # フォームからデータを取得
    outline_id = int(datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'))
    date = request.form.get('date')
    time_category = request.form.get('time_category')

    # DataStoreに格納
    if date and time_category:
        key1 = client.key('Outline')  # kind（テーブル）を指定し、keyを設定
        outline1 = datastore.Entity(key1)  # エンティティ（行）を指定のkeyで作成
        outline1.update({  # エンティティに入れるデータを指定
            'outline_id': outline_id,  # 日時をidとする
            'date': date,
            'time_category': time_category
        })
        client.put(outline1)  # DataStoreへ送信

        ##########
        key2 = client.key('Outline_yacht_player')
        outline2 = datastore.Entity(key2)
        outline2.update({
                        'outline_id': outline_id
        })
        client.put(outline2)

    #TOPページで、入力せずに追加ボタンを押した場合は、TOPに戻る
    else:
        return redirect(url_for('top'))

    #新規で作成したエンティティの読み込み
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', outline_id)
    target_outline1 = list(query1.fetch())[0]

    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', outline_id)
    target_outline2 = list(query2.fetch())

    #ドラムロールに表示する項目
    time_categories = ("-", "午前", "午後", "１部", "２部", "３部")
    wind_speeds = range(0,21)
    wind_directions = range(0, 360)
    sizes = ("-", "小", "中", "大")
    sea_surfaces = ("-", "フラット", "チョッピー", "高波")

    query_yacht = client.query(kind='Yacht')
    yacht_numbers = list(query_yacht.fetch())

    query_device = client.query(kind='Device')
    device_names = list(query_device.fetch())

    query_player = client.query(kind='Player')
    player_names = list(query_player.fetch())

    query_menu = client.query(kind='Menu')
    training_menus = list(query_menu.fetch())


    return render_template('show_outline.html', title="練習概要入力",\
                            target_outline1=target_outline1, target_outline2=target_outline2,\
                            wind_speeds=wind_speeds, wind_directions=wind_directions,\
                            time_categories=time_categories, sizes=sizes, sea_surfaces=sea_surfaces,\
                            training_menus=training_menus, yacht_numbers=yacht_numbers,\
                            player_names=player_names, device_names=device_names)


@app.route("/outline/mod_outline/<int:target_outline_id>", methods=['POST'])
def mod_outline(target_outline_id):
    """
    練習概要ページのデータを修正・更新
    """
    #日付、時間、風、波、練習メニューの値をクエリ実行して取得
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', int(target_outline_id))
    outline1 = list(query1.fetch())[0]

    #日付、時間、風、波、練習メニューの値をshow_outline.htmlから取得
    date = request.form.get('date')
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')
    timecategory = request.form.get('timecategory')
    windspeedmin = request.form.get('windspeedmin')
    windspeedmax = request.form.get('windspeedmax')
    winddirectionmin = request.form.get('winddirectionmin')
    winddirectionmax = request.form.get('winddirectionmax')
    windspeedchange = request.form.get('windspeedchange')
    seasurface = request.form.get('seasurface')
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

    if not outline1:
        raise ValueError(
            'Outline {} does not exist.'.format(outline1))

    outline1.update({
        'date': date,
        'start_time': starttime,
        'end_time': endtime,
        'time_category': timecategory,
        'wind_speed_min': int(windspeedmin),
        'wind_speed_max': int(windspeedmax),
        'wind_direction_min': int(winddirectionmin),
        'wind_direction_max': int(winddirectionmax),
        'wind_speed_change': str(windspeedchange),
        'sea_surface': str(seasurface),
        'swell': str(swell),
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

    client.put(outline1)

    #艇番、スキッパー、クルーの値をクエリ実行して取得
    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', int(target_outline_id))
    outline2s = list(query2.fetch())

    #show_outline.htmlから取得した値を変数に代入
    for i,outline2 in enumerate(outline2s):
        yachtnumber = request.form.get('yachtnumber'+str(i))
        devicename = request.form.get('devicename'+str(i))
        skipper1 = request.form.get('skipper1'+str(i))
        skipper2 = request.form.get('skipper2'+str(i))
        skipper3 = request.form.get('skipper3'+str(i))
        crew1 = request.form.get('crew1'+str(i))
        crew2 = request.form.get('crew2'+str(i))
        crew3 = request.form.get('crew3'+str(i))

        if not outline2:
            raise ValueError(
                'Outline {} does not exist.'.format(outline2))

        outline2.update({
            'yacht_number': int(yachtnumber),
            'device_name': str(devicename),
            'skipper1': str(skipper1),
            'skipper2': str(skipper2),
            'skipper3': str(skipper3),
            'crew1': str(crew1),
            'crew2': str(crew2),
            'crew3': str(crew3)
        })

        client.put(outline2)

    return redirect(url_for('top'))



@app.route("/outline/del_outline/<int:target_outline_id>", methods=['POST'])
def del_outline(target_outline_id):
    """
    練習概要ページの削除（動作テスト未）
    """

    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', int(target_outline_id))
    outline1 = list(query1.fetch())[0] #python形式のkey.idに変換
    key1 = outline1.key.id #idを取得
    client.delete(key1)

    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', int(target_outline_id))
    outline2s = list(query2.fetch())
    for outline2 in outline2s:
        key2 = outline2.key.id
        client.delete(key2)

    return redirect(url_for('top'))


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
    year = int(request.form.get('year'))
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

    return redirect(url_for('top'))


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
    year = int(request.form.get('year'))


    with client.transaction():
        key = client.key('Player', player_id)
        player = client.get(key)

        if not player:
            raise ValueError(
                'Player {} does not exist.'.format(player_id))

        player.update({
            'player_name' : str(playername),
            'admission_year' : int(year)
        })

        client.put(player)

    return redirect(url_for('top'))


@app.route("/admin/delplayer/<int:player_id>", methods=['POST'])
def del_player(player_id):
    """
    選手データの削除

    Return: TOPページに戻る
    """
    key = client.key('Player', player_id)
    client.delete(key)

    return redirect(url_for('top'))


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
    yachtno = int(request.form.get('yachtno'))
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

    return redirect(url_for('top'))



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
            'yacht_no': int(yachtno),
            'yacht_class': yachtclass
        })

        client.put(yacht)

    return redirect(url_for('top'))


@app.route("/admin/delyacht/<int:yacht_id>", methods=['POST'])
def del_yacht(yacht_id):
    """
    ヨットデータの削除

    Return: TOPページに戻る
    """

    key = client.key('Yacht', yacht_id)
    client.delete(key)

    return redirect(url_for('top'))


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

    return redirect(url_for('top'))

                           
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

    return redirect(url_for('top'))


@app.route("/admin/deldevice/<int:device_id>", methods=['POST'])
def del_device(device_id):
    """
    デバイス情報の削除

    Return:TOPページに戻る
    """
    key = client.key('Device', device_id)
    client.delete(key)

    return redirect(url_for('top'))

                           
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
    """
    menu_name = request.form.get('menu')

    if menu_name:
        key = client.key('Menu')
        menu = datastore.Entity(key)
        menu.update({
            'training_menu': menu_name
        })
        client.put(menu)

    return redirect(url_for('top'))

                           
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

    return redirect(url_for('top'))

                           
@app.route("/admin/delmenu/<int:menu_id>", methods=['POST'])
def del_menu(menu_id):
    """
    練習メニューの削除

    Return: TOPページに戻る
    """
    key = client.key('Menu', menu_id)
    client.delete(key)

    return redirect(url_for('top'))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
