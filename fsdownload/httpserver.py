from core.modules.controllers import *
from flask import request, jsonify
from core.modules.job import delete_expired_users
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

SCAN_TYPE = 'scan'
READ_TYPE = 'read'
INVALID_TOKEN_MESSAGE = 'Token 无效'
LOGIN_SUCCESS_MESSAGE = '登录成功'
EMPTY_CREDENTIALS_MESSAGE = '用户名或密码为空'
INVALID_CREDENTIALS_MESSAGE = '用户名或密码错误'

scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_expired_users, args=[app], trigger="interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())
delete_expired_users(app)


def create_response(code, message=None, type_value=None, token=None):
    response = {"code": code}
    if message:
        response["message"] = message
    if type_value:
        response["type"] = type_value
    if token:
        response["token"] = token
    return response


@app.route('/login/doLogin', methods=['POST'])
def do_login():
    print('Request URL:', request.url)
    print('Request Form Data:', request.form)

    username = request.form.get('username')
    password = request.form.get('pwd')
    type_value = request.form.get('type')

    if not username or not password:
        return jsonify(create_response("0", EMPTY_CREDENTIALS_MESSAGE))

    user = User.query.filter_by(name=username).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
        user.type = type_value  # 保存 type 到数据库
        db.session.commit()
        return jsonify(create_response("1", LOGIN_SUCCESS_MESSAGE, token=user.token))
    else:
        return jsonify(create_response("0", INVALID_CREDENTIALS_MESSAGE))


@app.route('/login/getInfo', methods=['POST'])
def get_info():
    print('Request URL:', request.url)
    print('Request Form Data:', request.form)

    token = request.form.get('token')
    if not token:
        return jsonify(create_response("0", INVALID_TOKEN_MESSAGE))

    user = User.query.filter_by(token=token).first()
    if user:
        if user.type == SCAN_TYPE:
            user.type = READ_TYPE
        else:
            user.type = SCAN_TYPE
        print(user.type)
        db.session.commit()
        return jsonify(create_response("1", type_value=user.type))
    else:
        return jsonify(create_response("0", INVALID_TOKEN_MESSAGE))



if __name__ == "__main__":
    

    app.run(debug=False, host='0.0.0.0', port=5555)
