from models.like import Like
from database.db import db

def add_like(user_id, movie_id):

    # Vérifier si l'utilisateur a déjà liké ce film
    existing_like = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing_like:
        return existing_like
    
    # Créer un nouveau like
    like = Like(user_id=user_id, movie_id=movie_id)
    db.session.add(like)
    db.session.commit()
    return like

def remove_like(user_id, movie_id):

    like = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
    return like

def get_likes_by_movie(movie_id):

    return Like.query.filter_by(movie_id=movie_id).all()

def get_likes_by_user(user_id):
 
    return Like.query.filter_by(user_id=user_id).all()

def check_user_liked_movie(user_id, movie_id):
 
    like = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    return like is not None