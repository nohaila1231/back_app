from models.watchlist import Watchlist
from database.db import db

def add_to_watchlist(user_id, movie_id):
    """
    Ajoute un film à la watchlist d'un utilisateur.
    
    Args:
        user_id: ID de l'utilisateur
        movie_id: ID du film
        
    Returns:
        Objet Watchlist créé
    """
    watchlist = Watchlist(user_id=user_id, movie_id=movie_id)
    db.session.add(watchlist)
    db.session.commit()
    return watchlist

def remove_from_watchlist(user_id, movie_id):
    """
    Supprime un film de la watchlist d'un utilisateur.
    
    Args:
        user_id: ID de l'utilisateur
        movie_id: ID du film
        
    Returns:
        Objet Watchlist supprimé ou None si non trouvé
    """
    watchlist = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if watchlist:
        db.session.delete(watchlist)
        db.session.commit()
    return watchlist

def get_user_watchlist(user_id):
    """
    Récupère la watchlist complète d'un utilisateur.
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        Liste des objets Watchlist pour cet utilisateur
    """
    return Watchlist.query.filter_by(user_id=user_id).all()

def check_movie_in_watchlist(user_id, movie_id):
    """
    Vérifie si un film est dans la watchlist d'un utilisateur.
    
    Args:
        user_id: ID de l'utilisateur
        movie_id: ID du film
        
    Returns:
        True si le film est dans la watchlist, False sinon
    """
    watchlist = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    return watchlist is not None

def get_watchlist_item(user_id, movie_id):
    """
    Récupère un élément spécifique de la watchlist.
    
    Args:
        user_id: ID de l'utilisateur
        movie_id: ID du film
        
    Returns:
        Objet Watchlist ou None si non trouvé
    """
    return Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()