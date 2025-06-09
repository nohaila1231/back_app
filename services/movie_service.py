from repositories.movie_repository import get_all_movies, get_movie_by_id, create_movie, update_movie, delete_movie
from services.tmdb_service import get_movie_from_tmdb, get_or_create_movie as tmdb_get_or_create

def get_movies():
    try:
        return get_all_movies()
    except Exception as e:
        print(f"Erreur lors de la récupération des films : {e}")
        return []

def get_movie(movie_id):
    try:
        return get_movie_by_id(movie_id)
    except Exception as e:
        print(f"Erreur lors de la récupération du film {movie_id} : {e}")
        return None

def add_movie(title, overview, poster_path, genres, popularity, release_date):
    try:
        if not title:
            raise ValueError("Le champ title est obligatoire.")
        return create_movie(title, overview, poster_path, genres, popularity, release_date)
    except Exception as e:
        print(f"Erreur lors de l'ajout du film : {e}")
        return None

# services/movie_service.py (version corrigée)
def get_or_create_movie(movie_id):
    try:
        # Vérifie si le film existe déjà en base
        movie = get_movie(movie_id)
        if movie:
            return movie, False
       
        tmdb_data = get_movie_from_tmdb(movie_id)
        if not tmdb_data:
            return None, False
        
        # Crée le film en base
        new_movie= create_movie(
            id=movie_id,
            title=tmdb_data['title'],
            overview=tmdb_data['overview'],
            poster_path=tmdb_data['poster_path'],
            genres=tmdb_data['genres'],
            popularity=tmdb_data['popularity'],
            release_date=tmdb_data['release_date']
        )
        return new_movie ,True
    except Exception as e:
        print(f"Erreur get_or_create_movie: {str(e)}")
        return None, False

def edit_movie(movie_id, title, overview, poster_path, genres, popularity, release_date):
    try:
        return update_movie(movie_id, title, overview, poster_path, genres, popularity, release_date)
    except Exception as e:
        print(f"Erreur lors de la mise à jour du film {movie_id} : {e}")
        return None

def remove_movie(movie_id):
    try:
        return delete_movie(movie_id)
    except Exception as e:
        print(f"Erreur lors de la suppression du film {movie_id} : {e}")
        return None