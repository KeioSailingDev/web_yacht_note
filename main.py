#標準ライブラリ
import os

#外部パッケージ
from flask import Flask
from flask_bootstrap import Bootstrap
from google.cloud import storage

# 分割先のコードをインポートする
from controllers.admin import admin_c
from controllers.outline import outline_c
from controllers.ranking import ranking_c
from controllers.how_to_use import how_to_use_c
from controllers.demand import demand_c
from controllers.top import top_c
# from controllers.error import error_c

# 環境変数を開発用と本番用で切り替え
os.environ['PROJECT_ID'] = 'webyachtnote'  #本番用
os.environ['LOG_TABLE'] = 'webyachtnote.smartphone_log.sensorlog'  #本番用
os.environ['HTML_TABLE'] = "webyachtnote.smartphone_log.log_map"  #本番用
os.environ['MAP_BUCKET'] = "gps_map"  #本番用
# os.environ['PROJECT_ID'] = 'web-yacht-note-208313'  # 開発用
# os.environ['LOG_TABLE'] = 'web-yacht-note-208313.smartphone_log.sensorlog'  # 開発用
# os.environ['HTML_TABLE'] = "web-yacht-note-208313.smartphone_log.log_map"  # 開発用
# os.environ['MAP_BUCKET'] = "gps_map_dev"  # 開発用

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# アプリケーションを作成
bootstrap = Bootstrap(app)

# cloud storageのクライアント
storage_client = storage.Client()
bucket = storage_client.get_bucket(os.environ.get('MAP_BUCKET'))

# 分割先のコントローラー(Blueprint)を登録する
app.register_blueprint(admin_c)
app.register_blueprint(outline_c)
app.register_blueprint(ranking_c)
app.register_blueprint(how_to_use_c)
app.register_blueprint(demand_c)
app.register_blueprint(top_c)
# app.register_blueprint(error_c)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
