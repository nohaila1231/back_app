# models/user.py
from database.db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Ajout du champ created_at
    
    def to_dict(self):
        """Convertir un objet User en dictionnaire."""
        return {
            'id': self.id,
            'fullname': self.fullname,
            'email': self.email,
            'image': self.image,
            'created_at': self.created_at.isoformat() if self.created_at else None  # Ajout du champ created_at
        }