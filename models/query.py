from gcloud import datastore
import os

project_id = os.environ.get('PROJECT_ID')
client = datastore.Client(project_id)


def get_outline_selections():

    # 時間帯の選択肢一覧
    time_categories = ("午前", "午後", "１部", "２部", "３部", "その他")

    # 風速の値一覧
    wind_speeds = range(0, 21)

    # 風向の値一覧
    wind_directions = ['北', '北東', '東', '南東', '南', '南西', '西', '北西']

    # うねりと風速変化の項目
    sizes = ("小", "中", "大")

    # 海面の項目一覧
    sea_surfaces = ("フラット", "チョッピー", "高波")

    # 艇番の一覧を取得
    query_yacht = client.query(kind='Yacht')
    yacht_numbers = list(query_yacht.fetch())

    # デバイス機種名の一覧を取得
    query_device = client.query(kind='Device')
    device_names = list(query_device.fetch())

    # ドラムロール表示用に、部員の一覧を取得
    query_player = client.query(kind='Player')
    player_names = list(query_player.fetch())

    # ドラムロール表示用に、練習メニューの一覧を取得
    query_menu = client.query(kind='Menu')
    training_menus = list(query_menu.fetch())

    outline_selections = [time_categories, wind_speeds, wind_directions, sizes, sea_surfaces, \
                          yacht_numbers, player_names, device_names, training_menus]

    return outline_selections


def get_outline_entities(target_outline_id):
    query1 = client.query(kind='Outline')
    query1.add_filter('outline_id', '=', int(target_outline_id))

    # 成功するまで実行
    for _ in range(10):
        while True:
            try:
                target_outline1 = list(query1.fetch())[0]
            except:
                pass
            break

    query2 = client.query(kind='Outline_yacht_player')
    query2.add_filter('outline_id', '=', int(target_outline_id))

    # 成功するまで実行
    for _ in range(10):
        while True:
            try:
                target_outline2 = list(query2.fetch())
            except:
                pass
            break

    target_entities = [target_outline1, target_outline2]

    return target_entities


def get_user_comments(target_outline_id):
    query = client.query(kind='Comment')
    query.add_filter('outline_id', '=', int(target_outline_id))
    user_comments = list(query.fetch())
    sorted_comments = sorted(user_comments, key=lambda user_comment: user_comment["created_date"], reverse=True)

    return sorted_comments

def fetch_retry(query_, num=20):
    # 成功するまで実行
    for _ in range(num):
        while True:
            try:
                res = query_.fetch()
            except:
                pass
            break
    return res
