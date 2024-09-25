from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from core import app

db = SQLAlchemy(app)

class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(60))
    token = db.Column(db.String(128), unique=True)
    notes = db.Column(db.Text())
    type = db.Column(db.String(10))
    expired_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return '<name:{}>'.format(self.name)


class Admin(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return '<Admin: {}>'.format(self.username)
