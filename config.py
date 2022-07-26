from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Config:
    SECRET_KEY = environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///log.db'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = environ.get('OPENAI_API_KEY')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'