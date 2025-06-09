from models.comment import Comment
from models.comment_like import CommentLike
from database.db import db
from sqlalchemy.orm import joinedload

def add_comment(user_id, movie_id, content, parent_id=None):
    """Ajoute un commentaire ou une réponse à un film."""
    try:
        comment = Comment(
            user_id=user_id, 
            movie_id=movie_id, 
            content=content,
            parent_id=parent_id
        )
        db.session.add(comment)
        db.session.commit()
        return comment
    except Exception as e:
        db.session.rollback()
        print(f"Error adding comment: {e}")
        return None

def get_comments_by_movie(movie_id):
    """Récupère tous les commentaires principaux d'un film avec leurs réponses."""
    try:
        return Comment.query.filter_by(
            movie_id=movie_id, 
            parent_id=None
        ).options(
            joinedload(Comment.user),
            joinedload(Comment.likes),
            joinedload(Comment.replies).joinedload(Comment.user),
            joinedload(Comment.replies).joinedload(Comment.likes)
        ).order_by(Comment.created_at.desc()).all()
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []

def get_comment_by_id(comment_id):
    """Récupère un commentaire par son ID."""
    try:
        return Comment.query.options(
            joinedload(Comment.user),
            joinedload(Comment.likes)
        ).get(comment_id)
    except Exception as e:
        print(f"Error fetching comment by ID: {e}")
        return None

def update_comment(comment_id, content):
    """Met à jour un commentaire."""
    try:
        comment = Comment.query.get(comment_id)
        if comment:
            comment.content = content
            comment.updated_at = db.func.now()
            db.session.commit()
        return comment
    except Exception as e:
        db.session.rollback()
        print(f"Error updating comment: {e}")
        return None

def delete_comment(comment_id):
    """Supprime un commentaire et toutes ses réponses."""
    try:
        comment = Comment.query.get(comment_id)
        if comment:
            db.session.delete(comment)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting comment: {e}")
        return False

def like_comment(user_id, comment_id):
    """Ajoute un like à un commentaire."""
    try:
        # Vérifier si le like existe déjà
        existing_like = CommentLike.query.filter_by(
            user_id=user_id, 
            comment_id=comment_id
        ).first()
        
        if existing_like:
            return existing_like
        
        like = CommentLike(user_id=user_id, comment_id=comment_id)
        db.session.add(like)
        db.session.commit()
        return like
    except Exception as e:
        db.session.rollback()
        print(f"Error liking comment: {e}")
        return None

def unlike_comment(user_id, comment_id):
    """Supprime un like d'un commentaire."""
    try:
        like = CommentLike.query.filter_by(
            user_id=user_id, 
            comment_id=comment_id
        ).first()
        
        if like:
            db.session.delete(like)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error unliking comment: {e}")
        return False

def is_comment_liked_by_user(user_id, comment_id):
    """Vérifie si un commentaire est liké par un utilisateur."""
    try:
        return CommentLike.query.filter_by(
            user_id=user_id, 
            comment_id=comment_id
        ).first() is not None
    except Exception as e:
        print(f"Error checking if comment is liked: {e}")
        return False

def get_comment_likes_count(comment_id):
    """Récupère le nombre de likes d'un commentaire."""
    try:
        return CommentLike.query.filter_by(comment_id=comment_id).count()
    except Exception as e:
        print(f"Error getting likes count: {e}")
        return 0
