#標準ライブラリ
import os
from datetime import datetime

#外部パッケージ
from flask import Flask, render_template, Blueprint, url_for, request, redirect
from google.cloud import datastore

#他スクリプト
from controllers import query

# "admin"という名前でBlueprintオブジェクトを生成します
admin_c = Blueprint('admin_c', __name__)

client = datastore.Client()

@admin_c.route("/admin/top")
def admin_top():
    """
    管理ページのルートページ
    """
    return render_template('admin_top.html')


@admin_c.route("/admin/player")
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


@admin_c.route("/admin/addplayer", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_player'))


@admin_c.route("/admin/showplayer/<int:player_id>", methods=['GET'])
def show_player(player_id):
    """選手データの変更画面に移動"""

    key = client.key('Player', player_id)
    target_player = client.get(key)

    #入学年の一覧
    this_year = (datetime.now()).year
    admission_years = list(range(this_year-10, this_year+10))

    return render_template('show_player.html', title='ユーザー詳細',\
    target_player=target_player, admission_years=admission_years)


@admin_c.route("/admin/modplayer/<int:player_id>", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_player'))


@admin_c.route("/admin/delplayer/<int:player_id>", methods=['POST'])
def del_player(player_id):
    """選手データの削除"""

    key = client.key('Player', player_id)
    client.delete(key)

    return redirect(url_for('admin_c.admin_player'))

@admin_c.route("/admin/yacht")
def admin_yacht():
    """
    ヨットの管理画面の表示
    """
    query_y = client.query(kind='Yacht')
    yachts_list = list(query.fetch_retry(query_y))
    sorted_yachts = sorted(yachts_list, key=lambda yacht: yacht["yacht_no"])

    return render_template('admin_yacht.html', title = 'ヨット管理', sorted_yachts = sorted_yachts)

@admin_c.route("/admin/addyacht", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_yacht'))

@admin_c.route("/admin/showyacht/<int:yacht_id>", methods=['GET'])
def show_yacht(yacht_id):
    """ヨットデータの変更画面に移動"""
    key = client.key('Yacht', yacht_id)
    target_yacht = client.get(key)

    return render_template('show_yacht.html', title='ユーザー詳細', target_yacht=target_yacht)

@admin_c.route("/admin/modyacht/<int:yacht_id>", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_yacht'))

@admin_c.route("/admin/delyacht/<int:yacht_id>", methods=['POST'])
def del_yacht(yacht_id):
    """ヨットデータの削除"""
    key = client.key('Yacht', yacht_id)
    client.delete(key)

    return redirect(url_for('admin_c.admin_yacht'))



@admin_c.route("/admin/device")
def admin_device():
    """デバイス管理画面の表示"""

    query_d = client.query(kind='Device')
    devices_list = list(query.fetch_retry(query_d))
    sorted_devices = sorted(devices_list, key=lambda device: device["device_id"])

    return render_template('admin_device.html', title='デバイス管理', sorted_devices=sorted_devices)

@admin_c.route("/admin/adddevice", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_device'))

@admin_c.route("/admin/showdevice/<int:device_id>", methods=['GET'])
def show_device(device_id):
    """デバイス情報の変更画面に移動"""

    key = client.key('Device', device_id)
    target_device = client.get(key)

    return render_template('show_device.html', title='デバイス詳細', target_device=target_device)

@admin_c.route("/admin/moddevice/<int:device_id>", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_device'))

@admin_c.route("/admin/deldevice/<int:device_id>", methods=['POST'])
def del_device(device_id):
    """デバイス情報の削除"""

    key = client.key('Device', device_id)
    client.delete(key)

    return redirect(url_for('admin_c.admin_device'))


@admin_c.route("/admin/menu")
def admin_menu():
    """練習メニューの管理画面を表示"""

    query_m = client.query(kind='Menu')
    menus_list = list(query.fetch_retry(query_m))
    sorted_menus = sorted(menus_list, key=lambda menu: menu["training_menu"])

    return render_template('admin_menu.html', title='練習メニュー', sorted_menus=sorted_menus)

@admin_c.route("/admin/addmenu", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_menu'))

@admin_c.route("/admin/showmenu/<int:menu_id>", methods=['GET'])
def show_menu(menu_id):
    """練習メニューの変更画面を表示"""

    key = client.key('Menu', menu_id)
    target_menu = client.get(key)

    return render_template('show_menu.html', title='練習メニュー詳細', target_menu=target_menu)

@admin_c.route("/admin/modmenu/<int:menu_id>", methods=['POST'])
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

    return redirect(url_for('admin_c.admin_menu'))

@admin_c.route("/admin/delmenu/<int:menu_id>", methods=['POST'])
def del_menu(menu_id):
    """練習メニューの削除"""

    key = client.key('Menu', menu_id)
    client.delete(key)

    return redirect(url_for('admin_c.admin_menu'))
