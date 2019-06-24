#
# from flask import Blueprint, render_template, abort
#
# # "error_c"という名前でBlueprintオブジェクトを生成します
# error_c = Blueprint('error_c', __name__)
#
# @error_c.app_errorhandler(401)
# @error_c.app_errorhandler(403)
# @error_c.app_errorhandler(404)
# @error_c.app_errorhandler(500)
# def error_handler(error):
#     print(error.code)
#     if error.code == 404:
#         error_message = "ページが存在しませんm(_ _)m"
#     elif error.code == 500:
#         error_message = "サーバーエラーが発生していますm(_ _)m。何度かページを更新すると改善することがあります。"
#     else:
#         error_message = "エラーが発生しました"
#     print(error_message)
#
#     return render_template("error.html", error_message=error_message), error.code
