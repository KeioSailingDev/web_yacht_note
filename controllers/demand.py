
#外部パッケージ
from flask import render_template, Blueprint
from google.cloud import datastore

#スクリプト
from controllers import query

# "demand_c"という名前でBlueprintオブジェクトを生成します
demand_c = Blueprint('demand_c', __name__)

# DataStoreに接続するためのオブジェクトを作成
client = datastore.Client()

@demand_c.route("/demand")
def demand():
    """要望ページ"""
    # 練習ノートの一覧を取得
    query1 = client.query(kind='Demand')
    demands = list(query.fetch_retry(query1, num=20))
    # フィルター
    return render_template('demand.html', demands=demands)
