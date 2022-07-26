from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# database models
class User(UserMixin, db.Model):
    __tablename__ = 'flasklogin-users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), primary_key=False, nullable=False, unique=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

# command log
class Log(db.Model):
    __tablename__ = 'command-code-log'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(100))
    user = db.Column(db.String(100))
    command = db.Column(db.String(1000))
    codeblock = db.Column(db.String(1000))
    feedback = db.Column(db.String(1000))
    times_edited = db.Column(db.Integer)

    def __init__(self, timestamp, command, codeblock, feedback):
        self.timestamp = timestamp
        self.user = User.username
        self.command = command
        self.codeblock = codeblock
        self.feedback = feedback
        self.times_edited = 0

