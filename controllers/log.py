
from flask import Blueprint


log_c = Blueprint('log_c', __name__)


class log_insert(object):
    @log_c.route("/log", methods=['POST'])
    def log_insert_bigquery(self):
        return 0
