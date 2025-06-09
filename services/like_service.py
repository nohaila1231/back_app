from repositories.like_repository import add_like, remove_like, get_likes_by_user as repo_get_likes_by_user
from services.movie_service import get_or_create_movie

def like_movie(user_id, movie_id):
    return add_like(user_id, movie_id)

def unlike_movie(user_id, movie_id):
    return remove_like(user_id, movie_id)

def get_likes_by_user(user_id):
    """
    Récupère tous les likes d'un utilisateur.
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        Liste des objets Like pour cet utilisateur
    """
    return repo_get_likes_by_user(user_id)
