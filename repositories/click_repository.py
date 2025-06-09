from models.click import Click
from database.db import db

def add_click(user_id, movie_id):
    """
    Ajoute un clic pour un utilisateur sur un film
    """
    try:
        click = Click(user_id=user_id, movie_id=movie_id)
        db.session.add(click)
        db.session.commit()
        return click
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'ajout du clic: {str(e)}")
        return None

def get_clicks_by_user(user_id):
    """
    Récupère tous les clics d'un utilisateur
    """
    return Click.query.filter_by(user_id=user_id).all()

def get_clicks_by_movie(movie_id):
    """
    Récupère tous les clics pour un film
    """
    return Click.query.filter_by(movie_id=movie_id).all()
