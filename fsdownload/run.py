from httpserver import *
# 关闭无用输日志
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
# app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

if __name__ == '__main__':
    # 初始化数据库
    # db.create_all()
    app.run(debug=False, host='0.0.0.0', port=5555)
