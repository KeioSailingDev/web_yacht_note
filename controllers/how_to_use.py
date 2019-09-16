from flask import Blueprint, render_template

# "how_to_use_c"という名前でBlueprintオブジェクトを生成します
how_to_use_c = Blueprint('how_to_use_c', __name__)

@how_to_use_c.route("/how_to_use")
def how_to_use():
    """使い方ページ"""

    page_title = "使い方"

    return render_template('how_to_use.html', page_title=page_title)
