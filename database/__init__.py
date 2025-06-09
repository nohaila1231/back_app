from flask import Flask
from .db import db
from dotenv import load_dotenv
import os

load_dotenv()  # charge les variables d'environnement depuis .env

def init_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app
