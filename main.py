from flask import Flask, render_template, request, redirect, url_for
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


#【練習概要のページを表示】2種類のOutline Kindのデータを持ってくる
@app.route("/outline/<int:target_outline_id>", methods=['GET'])
def outline_detail(target_outline_id):
    #日付,時間帯、波、風、練習メニューのデータを取得
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', int(target_outline_id))#outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    target_outline1 = list(query1.fetch())[0]#該当するエンティティは一つしかないため、[0]で一つ目を指定

    #艇番、スキッパー、クルーのデータを取得
    query2 = client.query(kind='Outline_yacht_player')#outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    query2.add_filter('outline_id', '=', int(target_outline_id))
    target_outline2 = list(query2.fetch())

    return render_template('outline_detail.html', title='練習概要', target_outline1=target_outline1, target_outline2=target_outline2)


#【練習概要ページの変更画面に遷移】
@app.route("/admin/show_outline/<int:target_outline_id>/", methods=['GET'])
def show_outline(target_outline_id):
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', target_outline_id)#outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    target_outline1 = list(query1.fetch())[0]#

    query2 = client.query(kind='Outline_yacht_player')#outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    query2.add_filter('outline_id', '=', target_outline_id)
    #query2.order = ['yacht_number']
    target_outline2 = list(query2.fetch())
    return render_template('show_outline.html', title='練習概要変更', target_outline1=target_outline1, target_outline2=target_outline2)


@app.route("/add_outline", methods=['POST'])
def add_outline():
    # フォームからデータを取得
    outline_id = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')
    time_category = request.form.get('time_category')

    # DataStoreに格納
    if starttime and endtime and time_category:
        key = client.key('Outline')  # kind（テーブル）を指定し、keyを設定
        outline = datastore.Entity(key)  # エンティティ（行）を指定のkeyで作成
        outline.update({  # エンティティに入れるデータを指定
            'outline_id': int(outline_id),  # 日時をidとする
            'date': starttime[0:10],
            'start_time': datetime.strptime(starttime, '%Y-%m-%dT%H:%M').astimezone(),
            'end_time': datetime.strptime(endtime, '%Y-%m-%dT%H:%M').astimezone(),
            'time_category': time_category,
        })
        client.put(outline)  # DataStoreへ送信
    else:
        return redirect(url_for('top'))

    # 元のページに戻る TODO 作成したページに移動に買える
    return redirect(url_for('top'))



#【練習概要ページの変更】
@app.route("/outline/mod_outline/<int:target_outline_id>", methods=['POST'])
def mod_outline(target_outline_id):

    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', target_outline_id)
    outline1 = list(query1.fetch())[0] #python形式のkey.idに変換

    #日付、
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

    outline1['date'] = date
    outline1['start_time'] = starttime
    outline1['end_time'] = endtime
    outline1['time_category'] = timecategory
    outline1['wind_speed_min'] = windspeedmin
    outline1['wind_speed_max'] = windspeedmax
    outline1['wind_direction_min'] = windspeedmin
    outline1['wind_direction_max'] = winddirectionmax
    outline1['wind_speed_change'] = windspeedchange
    outline1['sea_surface'] = seasurface
    outline1['sewll'] = swell
    outline1['training1'] = training1
    outline1['training2'] = training2
    outline1['training3'] = training3
    outline1['training4'] = training4
    outline1['training5'] = training5
    outline1['training6'] = training6
    outline1['training7'] = training7
    outline1['training8'] = training8
    outline1['training9'] = training9
    outline1['training10'] = training10
    outline1['training11'] = training11
    outline1['training12'] = training12
    outline1['training13'] = training13
    outline1['training14'] = training14
    outline1['training15'] = training15

    client.put(outline1)

    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', target_outline_id)
    query2.order('yacht_number')
    target_outline2 = list(query2.fetch())

    for i,outline2 in enumerate(target_outline2):
        yachtnumber = requset.form.get('yachtnumber'+i)
        skipper1 = request.form.get('skipper1'+i)
        skipper2 = request.form.get('skipper2'+i)
        skipper3 = request.form.get('skipper3'+i)
        crew1 = request.form.get('crew1'+i)
        crew2 = request.form.get('crew2'+i)
        crew3 = request.form.get('crew3'+i)

        if not outline2:
            raise ValueError(
                'Outline {} does not exist.'.format(outline2))

        outline2['yacht_number'] = yacht_number
        outline2['skipper1'] = skipper1
        outline2['skipper2'] = skipper2
        outline2['skipper3'] = skipper3
        outline2['crew1'] = crew1
        outline2['crew2'] = crew2
        outline2['crew3'] = crew3

        clinet.put(outline2)

    return redirect(url_for('top'))


# 【練習概要ページの削除】
# @app.route("/outline/del_outline/<int:target_outline_id>", methods=['POST'])
# def del_outline(outline1_id, outline2_id):
#     key1 = client.key('Outline', outline1_id)
#     key2 = client.key('Outline_yacht_player', outline2_id)
#     client.delete(key1, key2)
#
#     return redirect(url_for('top'))

#【選手の管理画面を表示】Datasotreから選手の情報を取得し、htmlに渡す
@app.route("/admin/player")
def admin_player():
    query = client.query(kind='Player')
    player_list = list(query.fetch())
    return render_template('admin_player.html', title='選手管理', player_list=player_list)

#【選手の追加】選手名、入学年、更新時間の３点を、既存のエンティティに上書きする
@app.route("/admin/addplayer", methods=['POST'])
def add_player():
    playername = request.form.get('playername')
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

#【選手データの変更画面を表示】特定のIDの選手データをhtmlに引き渡す
@app.route("/admin/showplayer/<int:player_id>", methods=['GET'])
def show_player(player_id):
    key = client.key('Player', player_id)
    target_player = client.get(key)

    return render_template('show_player.html', title='ユーザー詳細', target_player=target_player)

#【選手データの変更】選手名と入学年を更新する
@app.route("/admin/modplayer/<int:player_id>", methods=['POST'])
def mod_player(player_id):
    playername = request.form.get('playername')
    year = request.form.get('year')

    with client.transaction():
        key = client.key('Player', player_id)
        player = client.get(key)

        if not player:
            raise ValueError(
                'Player {} does not exist.'.format(player_id))

        player['player_name'] = str(playername) #選手名を上書き
        player['admission_year'] = int(year) #入学年を上書き

        client.put(player)

    return redirect(url_for('top'))

#【選手データの削除】特定のIDのエンティティを削除
@app.route("/admin/delplayer/<int:player_id>", methods=['POST'])
def del_player(player_id):
    key = client.key('Player', player_id)
    client.delete(key)

    return redirect(url_for('top'))

#【ヨットの管理画面を表示】Datastoreからヨットのデータを取得し、htmlに渡す
@app.route("/admin/yacht")
def admin_yacht():
    query = client.query(kind='Yacht')
    yacht_list = list(query.fetch())

    return render_template('admin_yacht.html', title = 'ヨット管理', yacht_list = yacht_list)


# 【ヨットデータの追加】艇番、艇種、更新日時の３点を追加する
@app.route("/admin/addyacht", methods=['POST'])
def add_yacht():
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


# 【ヨットデータの変更画面の表示】特定のIDのエンティティを取得し、htmlに引き渡す
@app.route("/admin/showyacht/<int:yacht_id>", methods=['GET'])
def show_yacht(yacht_id):
    key = client.key('Yacht', yacht_id)
    target_yacht = client.get(key)

    return render_template('show_yacht.html', title='ユーザー詳細', target_yacht=target_yacht)


# 【ヨットデータの変更】艇番と艇種を上書きし、修正する
@app.route("/admin/modyacht/<int:yacht_id>", methods=['POST'])
def mod_yacht(yacht_id):
    yachtno = request.form.get('yachtno')
    yachtclass = request.form.get('yachtclass')

    with client.transaction():
        key = client.key('Yacht', yacht_id)
        yacht = client.get(key)

        if not yacht:
            raise ValueError(
                'Yacht {} does not exist.'.format(yacht_id))

        yacht['yacht_no'] = int(yachtno) #艇番を上書き
        yacht['yacht_class'] = yachtclass #艇種を上書き

        client.put(yacht)

    return redirect(url_for('top'))

#【ヨットデータの削除】特定のIDのエンティティを削除
@app.route("/admin/delyacht/<int:yacht_id>", methods=['POST'])
def del_yacht(yacht_id):
    key = client.key('Yacht', yacht_id)
    client.delete(key)

    return redirect(url_for('top'))

#【デバイスの管理画面を表示】Datastoreからデバイスのデータを取得し、htmlに渡す
@app.route("/admin/device")
def admin_device():
    query = client.query(kind='Device')
    device_list = list(query.fetch())

    return render_template('admin_device.html', title='デバイス管理', device_list=device_list)

#【デバイスデータの追加】deviceno: 手動で割り振ることになるスマホのIDを示す　devicename: スマホの機種　スマホID, スマホ機種、更新日時の３点をhtmlに渡す
@app.route("/admin/adddevice", methods=['POST'])
def add_device():
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

#【デバイスデータの変更画面の表示】特定のIDのエンティティをhtmlに引き渡す
@app.route("/admin/showdevice/<int:device_id>", methods=['GET'])
def show_device(device_id):
    key = client.key('Device', device_id)
    target_device = client.get(key)

    return render_template('show_device.html', title='デバイス詳細', target_device=target_device)

#【デバイスデータの変更】特定のIDのエンティティに対して、スマホIDとスマホ機種の２点を上書きする
@app.route("/admin/moddevice/<int:device_id>", methods=['POST'])
def mod_device(device_id):
    deviceno = request.form.get('deviceno')
    devicename = request.form.get('devicename')

    with client.transaction():
        key = client.key('Device', device_id)
        device = client.get(key)

        if not device:
            raise ValueError(
                'Device {} does not exist.'.format(device_id))

        device['device_no'] = deviceno
        device['device_name'] = devicename #スマホ機種を上書き

        client.put(device)

    return redirect(url_for('top'))

#【デバイスデータの削除】特定のIDのエンティティをDatastoreから削除
@app.route("/admin/deldevice/<int:device_id>", methods=['POST'])
def del_device(device_id):
    key = client.key('Device', device_id)
    client.delete(key)

    return redirect(url_for('top'))

#【練習メニューの管理画面を表示】Datasotreから練習メニューの情報を取得し、htmlに渡す
@app.route("/admin/menu")
def admin_menu():
    query = client.query(kind='Menu')
    menu_list = list(query.fetch())
    return render_template('admin_menu.html', title='練習メニュー', menu_list=menu_list)

#【練習メニューの追加】練習メニューを、既存のエンティティに上書きする
@app.route("/admin/addmenu", methods=['POST'])
def add_menu():
    menu_name = request.form.get('menu')

    if menu_name:
        key = client.key('Menu')
        menu = datastore.Entity(key)
        menu.update({
            'training_menu': menu_name
        })
        client.put(menu)

    return redirect(url_for('top'))

#【練習メニューデータの変更画面を表示】特定のIDの練習メニューデータをhtmlに引き渡す
@app.route("/admin/showmenu/<int:menu_id>", methods=['GET'])
def show_menu(menu_id):
    key = client.key('Menu', menu_id)
    target_menu = client.get(key)

    return render_template('show_menu.html', title='練習メニュー詳細', target_menu=target_menu)

#【練習メニューデータの変更】練習メニューを更新する
@app.route("/admin/modmenu/<int:menu_id>", methods=['POST'])
def mod_menu(menu_id):
    menu_name = request.form.get('menu')

    with client.transaction():
        key = client.key('Menu', menu_id)
        menu = client.get(key)

        if not menu:
            raise ValueError(
                'Menu {} does not exist.'.format(menu_id))

        menu['training_menu'] = menu_name

        client.put(menu)

    return redirect(url_for('top'))

#【練習メニューデータの削除】特定のIDのエンティティを削除
@app.route("/admin/delmenu/<int:menu_id>", methods=['POST'])
def del_menu(menu_id):
    key = client.key('Menu', menu_id)
    client.delete(key)

    return redirect(url_for('top'))




if __name__ == '__main__':
    app.run(host='0.0.0.0')
