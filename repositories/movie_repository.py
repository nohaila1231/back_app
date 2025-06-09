from models.movie import Movie
from database.db import db
from datetime import datetime

def get_all_movies():
    """
    Récupère tous les films de la base de données.
    
    Returns:
        Liste des objets Movie
    """
    return Movie.query.all()

def get_movie_by_id(movie_id):
    """
    Récupère un film par son ID.
    
    Args:
        movie_id: ID du film
        
    Returns:
        Objet Movie ou None si non trouvé
    """
    return Movie.query.get(movie_id)

def get_movie_by_tmdb_id(tmdb_id):
    """
    Récupère un film par son ID TMDB.
    
    Args:
        tmdb_id: ID du film dans TMDB
        
    Returns:
        Objet Movie ou None si non trouvé
    """
    return Movie.query.filter_by(id=tmdb_id).first()

# repositories/movie_repository.py
def create_movie(id, title, overview, poster_path, genres, popularity, release_date):
    try:
        new_movie = Movie(
            id=id,
            title=title,
            overview=overview,
            poster_path=poster_path,
            genres=genres,
            popularity=popularity,
            release_date=release_date
        )
        db.session.add(new_movie)
        db.session.commit()
        return new_movie  # Retourne l'objet Movie
    except Exception as e:
        db.session.rollback()
        return None

def update_movie(movie_id, title, overview, poster_path, genres, popularity, release_date):

    movie = Movie.query.get(movie_id)
    if movie:
        movie.title = title
        movie.overview = overview
        movie.poster_path = poster_path
        movie.genres = genres
        movie.popularity = popularity
        movie.release_date = datetime.fromisoformat(release_date) if release_date else None
        db.session.commit()
    return movie

def delete_movie(movie_id):
    movie = Movie.query.get(movie_id)
    if movie:
        db.session.delete(movie)
        db.session.commit()
    return movie