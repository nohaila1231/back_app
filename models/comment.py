from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.db import db

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), nullable=True)
    content = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations - CORRECTION: Ajout de la relation likes manquante
    user = relationship("User", backref="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    likes = relationship("CommentLike", backref="comment", cascade="all, delete-orphan")

    def get_likes_count(self):
        """Méthode pour compter les likes"""
        try:
            return len(self.likes) if self.likes else 0
        except:
            return 0
    
    def is_liked_by_user(self, user_id):
        """Vérifier si un utilisateur a liké ce commentaire"""
        if not user_id:
            return False
        try:
            return any(like.user_id == user_id for like in self.likes) if self.likes else False
        except:
            return False

    def to_dict(self, include_replies=True, user_id=None):
        """Convertir en dictionnaire avec support user_id"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else (self.created_at.isoformat() if self.created_at else None),
            'user': self.user.to_dict() if self.user else None,
            'likes_count': self.get_likes_count(),
            'is_liked_by_user': self.is_liked_by_user(user_id) if user_id else False
        }
        
        if include_replies and hasattr(self, 'replies') and self.replies:
            result['replies'] = [reply.to_dict(include_replies=False, user_id=user_id) for reply in self.replies]
            result['replies_count'] = len(self.replies)
        else:
            result['replies_count'] = 0
        
        return result
    