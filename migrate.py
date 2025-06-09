from flask_migrate import Migrate
from app import app
from database.db import db

migrate = Migrate(app, db)

# Ce bloc permet à flask de trouver "app"
# Commande à utiliser : flask db init / migrate / upgrade
