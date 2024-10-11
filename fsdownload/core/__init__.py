from flask import Flask,request,render_template,url_for,redirect
import os
app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL')
assert database_url is not None, "DATABASE_URL is not set"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
  'pool_size': 10,
  'max_overflow': 100,
  'pool_recycle': 1800,
  'pool_pre_ping': True,
}
