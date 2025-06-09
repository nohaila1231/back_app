from sqlalchemy import Column, Integer, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from database.db import db

class Recommendation(db.Model):
    """Modèle pour stocker les recommandations générées par ML"""
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    score = db.Column(db.Float, nullable=False)  # Score de recommandation calculé par le modèle ML
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    
    # Relations
    user = relationship("User", backref="recommendations")
    movie = relationship("Movie", backref="recommendations")
    
    def to_dict(self):
        """Convertir un objet Recommendation en dictionnaire."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'score': self.score,
            'created_at': self.created_at,
            'movie': self.movie.to_dict() if self.movie else None
        }
