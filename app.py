from flask import Flask, render_template, request, redirect, url_for
from gcloud import datastore
from datetime import datetime, timedelta

# プロジェクトID
project_id = "web-yacht-note-208313"

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client(project_id)

# アプリケーションを作成
app = Flask(__name__)


@app.route('/')
def top():
    #
    # TOPページを表示したときの挙動
    #

    # 練習ノートの一覧を取得
    query = client.query(kind='Note')
    note_list = list(query.fetch())

    # 現在時刻を取得
    datetime_now = datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M')

    return render_template('top.html', title='ユーザ一覧',
                           note_list=note_list, datetime_now = datetime_now)

#【練習概要のページを表示】2種類のOutline Kindのデータを持ってくる
@app.route("/outline/<int:target_outline_id>", methods=['GET'])
def outline_detail(target_outline_id):
    #日付,時間帯、波、風、練習メニューのデータを取得
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', target_outline_id)
    target_outline1 = list(query1.fetch())[0]#該当エンティティは一つしかないため、[0]で一つ目を指定
    #outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    #取得したエンティティを変数に代入し、htmlファイルに渡す

    #艇番、スキッパー、クルーのデータを取得
    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', target_outline_id)
    target_outline2 = list(query2.fetch())
    #outline_idプロパティ内から、特定のoutline_idに一致するエンティティを取得
    #取得したエンティティを変数に代入し、htmlファイルに渡す
    #Outline_yacht_player Kindからは複数のエンティティを取得する為、listにしてデータを取得する

    return render_template('outline_detail.html', title='練習概要', target_outline1=target_outline1, target_outline2=target_outline2)

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

#【ヨットデータの追加】艇番、艇種、更新日時の３点を追加する
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

#【ヨットデータの変更画面の表示】特定のIDのエンティティを取得し、htmlに引き渡す
@app.route("/admin/showyacht/<int:yacht_id>", methods=['GET'])
def show_yacht(yacht_id):
    key = client.key('Yacht', yacht_id)
    target_yacht = client.get(key)

    return render_template('show_yacht.html', title='ユーザー詳細', target_yacht=target_yacht)

#【ヨットデータの変更】艇番と艇種を上書きし、修正する
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


@app.route("/add_note", methods=['POST'])
def add_note():
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')

    if starttime[0:10] == endtime[0:10]:
        notename = starttime[0:10] + "_" + starttime[11:13] + "-" + endtime[11:13]
    else:
        notename = starttime + endtime

    if starttime and endtime:
        key = client.key('Note') # kind（テーブル）を指定し、keyを設定
        note = datastore.Entity(key) # エンティティ（行）を指定のkeyで作成
        note.update({ # エンティティに入れるデータを指定
            'starttime': datetime.strptime(starttime, '%Y-%m-%dT%H:%M').astimezone(),
            'endtime': datetime.strptime(endtime, '%Y-%m-%dT%H:%M').astimezone(),
            'notename': notename
        })
        client.put(note) # DataStoreへ送信

    return redirect(url_for('top'))


@app.route("/note/<int:note_id>", methods=['GET'])
def show_note(note_id):
    key = client.key('Note', note_id)
    target_user = client.get(key)

    return render_template('show.html', title='ノート詳細', target_user=target_user)


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
