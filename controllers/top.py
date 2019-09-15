#外部パッケージ
from flask import Flask, render_template, url_for, request, Blueprint, redirect
from google.cloud import datastore
import pandas as pd

#他スクリプト
from controllers import query

top_c = Blueprint('top_c', __name__)

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client()

@top_c.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


@top_c.errorhandler(500)
def internal_server_error(error):
    return render_template('internal_server_error.html'), 500

@top_c.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/list')


@top_c.route('/list', methods=['GET', 'POST'])
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

    return render_template('top.html', title='Webヨットノート', page_title='練習ノート一覧',
                            outline_list=outline_list, outline_selections=outline_selections, form_default=form_values)
