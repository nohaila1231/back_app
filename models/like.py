from sqlalchemy import Column, Integer, String, Float, Date,ForeignKey ,func , JSON
from sqlalchemy.orm import relationship
from database.db import db
class Like(db.Model):
    """Modèle pour la table des likes"""
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = db.Column(db.Integer, ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    
    # Relations
    user = relationship("User", backref="likes")
    # movie = relationship("Movie", backref="likes")
    
    def to_dict(self):
        """Convertir un objet Like en dictionnaire."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'created_at': self.created_at,
            'user': self.user.to_dict() if self.user else None,
            'movie': self.movie.to_dict() if self.movie else None
        }
