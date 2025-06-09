from sqlalchemy import Column, Integer, String, ForeignKey, Date,func , JSON
from sqlalchemy.orm import relationship
from database.db import db
class Watchlist(db.Model):
    """Modèle pour la table des watchlists"""
    __tablename__ = 'watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    added_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    
    # Relations
    user = relationship("User", backref="watchlist_items")
    # movie = relationship("Movie", backref="watchlist_items")

    def to_dict(self):
        """Convertir un objet Watchlist en dictionnaire."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'added_at': self.added_at,
            'user': self.user.to_dict() if self.user else None,
            'movie': self.movie.to_dict() if self.movie else None
        }
