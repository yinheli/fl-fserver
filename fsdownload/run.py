from httpserver import *
# 关闭无用输日志
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
# app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def init_db():
    with app.app_context():
        import bcrypt
        db.create_all()

        # init admin user with username: admin, password: 123456
        Admin.query.delete()
        password = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt())
        admin = Admin(username='admin', password_hash=password.decode('utf-8'))
        db.session.add(admin)
        db.session.commit()

        print("init done")

if __name__ == '__main__':
    import sys
    if '--init-db' in sys.argv:
        init_db()
    else:
        app.run(debug=False, host='0.0.0.0', port=5555)
