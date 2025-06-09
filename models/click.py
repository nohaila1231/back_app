from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database.db import db

class Click(db.Model):
    """Modèle pour enregistrer les clics sur les films"""
    __tablename__ = 'clicks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    clicked_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    
    # Relations
    user = relationship("User", backref="clicks")
    movie = relationship("Movie", backref="clicks")
    
    def to_dict(self):
        """Convertir un objet Click en dictionnaire."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'clicked_at': self.clicked_at,
        }
