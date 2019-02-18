from flask import Blueprint, render_template

# "how_to_use_c"という名前でBlueprintオブジェクトを生成します
how_to_use_c = Blueprint('how_to_use_c', __name__)

@how_to_use_c.route("/how_to_use")
def how_to_use():
    """使い方ページ"""
    return render_template('how_to_use.html')
