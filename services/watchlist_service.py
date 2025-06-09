from repositories.watchlist_repository import add_to_watchlist, remove_from_watchlist, get_user_watchlist
from models.watchlist import Watchlist
from services.movie_service import get_or_create_movie
from database.db import db

def add_movie_to_watchlist(user_id, movie_id):    
    # Vérifiez si l'élément existe déjà dans la base de données
    existing_entry = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing_entry:
        # Si l'élément existe déjà, renvoyer l'entrée existante (pas de doublon)
        return existing_entry
   
    # Sinon, ajoutez une nouvelle entrée à la watchlist
    return add_to_watchlist(user_id, movie_id)

def remove_movie_from_watchlist(user_id, movie_id):
    return remove_from_watchlist(user_id, movie_id)

def get_user_watchlist_with_movies(user_id):
    """
    Récupère la watchlist d'un utilisateur avec les détails des films.
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        Liste des détails des films dans la watchlist
    """
    watchlist_items = get_user_watchlist(user_id)
    
    # Récupérer les détails des films pour chaque élément de la watchlist
    movies = []
    for item in watchlist_items:
        # Utiliser get_or_create_movie au lieu de get_movie_details
        movie, _ = get_or_create_movie(item.movie_id)
        if movie:
            movies.append(movie.to_dict() if hasattr(movie, 'to_dict') else movie)
    
    return movies
