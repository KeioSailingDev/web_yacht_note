#標準ライブラリ
import os
from datetime import datetime

#外部パッケージ
from flask import render_template, Blueprint, url_for
from google.cloud import datastore

#他スクリプト
from controllers import query

# "action"という名前でBlueprintオブジェクトを生成します
admin_c = Blueprint('admin', __name__)

project_id = os.environ.get('PROJECT_ID')
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
    player_list = list(query.fetch_retry(query_p))

    #「入学年」の一覧を取得
    this_year = (datetime.now()).year
    admission_years = list(range(this_year-10, this_year+10))

    return render_template('admin_player.html', title='選手管理', \
    player_list=player_list, admission_years=admission_years)


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

    return redirect(url_for('admin_player'))


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

    return redirect(url_for('admin_player'))


@admin_c.route("/admin/delplayer/<int:player_id>", methods=['POST'])
def del_player(player_id):
    """選手データの削除"""

    key = client.key('Player', player_id)
    client.delete(key)

    return redirect(url_for('admin_player'))
