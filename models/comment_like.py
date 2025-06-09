from database.db import db
from sqlalchemy import func

class CommentLike(db.Model):
    __tablename__ = 'comment_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    
    # Relations
    user = db.relationship("User", backref="comment_likes")
   
    
    # Contrainte unique pour éviter les doublons
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'comment_id': self.comment_id,
            'created_at': self.created_at,
            'user': self.user.to_dict() if self.user else None
        }