from gcloud import datastore
import os

client = datastore.Client()


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
    yacht_numbers = list(fetch_retry(query_yacht))

    # デバイス機種名の一覧を取得
    query_device = client.query(kind='Device')
    device_names = list(fetch_retry(query_device))

    # ドラムロール表示用に、部員の一覧を取得
    query_player = client.query(kind='Player')
    player_names = list(fetch_retry(query_player))

    # ドラムロール表示用に、練習メニューの一覧を取得
    query_menu = client.query(kind='Menu')
    training_menus = list(fetch_retry(query_menu))

    # 風向フィルター
    filter_selection_directions = [["北（北・北東・北西）", "compass_n"],
                                   ["東", "compass_e"],
                                   ["南（南・南東・南西）", "cpmpass_s"],
                                   ["西", "compass_w"]]

    # 風速フィルター
    filter_selection_speed = [["強風", "flag_l"], ["中風", "flag_m"],["軽風", "flag_s"]]

    # 海面フィルター
    filter_selection_wave = [["フラット", "wave_s"], ["チョッピー", "wave_m"], ["うねり", "wave_l"]]

    #練習時間オプション
    training_time = (10, 20, 30, 40, 50, 60)

    outline_selections = [time_categories, wind_speeds, wind_directions, sizes, sea_surfaces, \
                          yacht_numbers, player_names, device_names, training_menus,filter_selection_directions,
                          filter_selection_speed, filter_selection_wave, training_time]


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

    #コメントを最新順にする場合は、以下をコメントアウト
    sorted_comments = sorted(user_comments, key=lambda user_comment: user_comment["created_date"])

    return sorted_comments
