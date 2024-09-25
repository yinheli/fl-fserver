from flask import session
import bcrypt
import uuid
import hashlib
from core import *
from core.modules.data import *
from datetime import datetime, timezone, timedelta


DEFAULT_ERROR_MESSAGE = '发生错误'
ERROR_MESSAGE = "error_message"
LOGIN_REQUIRED = "请先登录"
USER_NOT_FOUND = "用户不存在"
LOGIN_PAGE = "login"
INDEX_PAGE = "index_page"
ERROR_PAGE = "error"
ADD_USER_PAGE = "add_user_page"
EDIT_PAGE = "edit_page"
LOGIN_SUCCESS = "登录成功"
FIELDS_REQUIRED = "所有字段都是必填的"
INVALID_CREDENTIALS = "用户名或密码不正确"
EMPTY_USERNAME_PASSWORD = "用户名和密码都是必填的"
EMPTY_NAME_NOTES = "名称和备注都是必填的"
USER_CREATION_FAILURE_MESSAGE = "用户创建失败"


def validate_form_data(*args):
    return all(arg and isinstance(arg, str) and arg.strip() for arg in args)


def hash_password(password):
    md5_hash = hashlib.md5(password.encode()).hexdigest()
    return bcrypt.hashpw(md5_hash.encode('utf-8'), bcrypt.gensalt())


@app.route('/')
def index_page():
    if 'admin_id' not in session:
        return redirect(url_for(LOGIN_PAGE))
    return render_template('index.html', data=enumerate(User.query.all(), 1))


@app.route('/add-user', methods=["POST", "GET"])
def add_data():
    if 'admin_id' not in session:
        return redirect(url_for(ERROR_PAGE, error_message=LOGIN_REQUIRED))

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        notes = request.form.get('notes')
        days_to_expire = request.form.get('days_to_expire', default=None, type=int)
        if days_to_expire is not None and days_to_expire <= 0:
            days_to_expire = None

        if not validate_form_data(name, password):
            return redirect(url_for(ERROR_PAGE, error_message=EMPTY_USERNAME_PASSWORD))

        try:
            hashed_password = hash_password(password)
            token = str(uuid.uuid4())
            expired_at = None
            if days_to_expire is not None:
                expired_at = datetime.now() + timedelta(days=days_to_expire)
            new_user = User(name=name, password_hash=hashed_password, token=token, notes=notes, expired_at=expired_at)
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            print(e)
            return redirect(url_for(ERROR_PAGE, error_message=USER_CREATION_FAILURE_MESSAGE))

        return redirect(url_for(INDEX_PAGE))

    return render_template('index.html', data=enumerate(User.query.all(), 1))


@app.route('/delete/<int:id>')
def delete_data(id):
    if 'admin_id' not in session:
        return redirect(url_for(ERROR_PAGE, error_message=LOGIN_REQUIRED))

    user = User.query.get(id)
    if not user:
        return redirect(url_for(ERROR_PAGE, error_message=USER_NOT_FOUND))

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for(INDEX_PAGE))


@app.route('/edit/<int:id>', methods=["GET", "POST"])
def edit_page(id):
    if 'admin_id' not in session:
        return redirect(url_for(ERROR_PAGE, error_message=LOGIN_REQUIRED))

    user = User.query.get(id)
    if not user:
        return redirect(url_for(ERROR_PAGE, error_message=USER_NOT_FOUND))
    
    days_to_expire = 0
    if user.expired_at is not None:
        days_to_expire = (user.expired_at - user.created_at).days + 1

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        notes = request.form.get('notes')
        days_to_expire = request.form.get('days_to_expire', default=None, type=int)
        if days_to_expire is not None and days_to_expire <= 0:
            days_to_expire = None

        if not validate_form_data(name, notes):
            return redirect(url_for(ERROR_PAGE, error_message=EMPTY_NAME_NOTES))

        user.name = name
        user.notes = notes
        if password and password.strip():
            user.password_hash = hash_password(password)

        if days_to_expire is not None:
            user.expired_at = datetime.now() + timedelta(days=days_to_expire)

        user.token = str(uuid.uuid4())
        db.session.commit()
        return redirect(url_for(INDEX_PAGE))

    return render_template('edit_page.html', name=user.name, notes=user.notes, expired_at=user.expired_at, days_to_expire=days_to_expire)


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not validate_form_data(username, password):
            return redirect(url_for(ERROR_PAGE, error_message=EMPTY_USERNAME_PASSWORD))

        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin.password_hash):
            session['admin_id'] = admin.id
            return redirect(url_for(INDEX_PAGE))
        else:
            return redirect(url_for(ERROR_PAGE, error_message=INVALID_CREDENTIALS))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for(LOGIN_PAGE))


@app.route('/change-password', methods=["POST", "GET"])
def change_password():
    if 'admin_id' not in session:
        return redirect(url_for(ERROR_PAGE, error_message=LOGIN_REQUIRED))

    if request.method == 'POST':
        username = request.form.get('username')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        if not validate_form_data(username, old_password, new_password):
            return redirect(url_for(ERROR_PAGE, error_message=FIELDS_REQUIRED))

        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.checkpw(old_password.encode('utf-8'), admin.password_hash):
            admin.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            db.session.commit()
            return redirect(url_for(LOGIN_PAGE))
        else:
            return redirect(url_for(ERROR_PAGE, error_message=INVALID_CREDENTIALS))

    return render_template('change_password.html')


@app.route('/error')
def error():
    error_message = request.args.get(ERROR_MESSAGE, DEFAULT_ERROR_MESSAGE)
    return render_template('error.html', error_message=error_message)
