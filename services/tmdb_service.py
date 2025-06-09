import requests
import json
from database.db import db
from models.movie import Movie

# Configuration TMDB
TMDB_API_KEY = "2dca580c2a14b55200e784d157207b4d"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_LANGUAGE = "fr-FR"

def get_movie_from_tmdb(movie_id):
    """Récupère les détails d'un film depuis l'API TMDB"""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": TMDB_LANGUAGE
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lever une exception si la réponse est un échec
        movie_data = response.json()
        
        # Extraire les genres et les formater en JSON pour stockage
        genres = []
        if "genres" in movie_data and movie_data["genres"]:
            genres = [genre["name"] for genre in movie_data["genres"]]
        
        # Créer un dictionnaire avec les données du film
        movie_info = {
            "title": movie_data.get("title"),
            "overview": movie_data.get("overview"),
            "poster_path": movie_data.get("poster_path"),
            "genres": genres,  # Convertir la liste en string JSON
            "popularity": movie_data.get("popularity"),
            "release_date": movie_data.get("release_date")
        }
        
        return movie_info
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération du film depuis TMDB: {e}")
        return None
def get_or_create_movie(movie_id):
    """Récupère ou crée un film dans la base de données"""
    # Vérifier si le film existe déjà dans la base de données
    movie = Movie.query.filter_by(id=movie_id).first()
    
    if movie:
        print(f"Film trouvé dans la base de données: {movie}")
        return movie, False  # Le film existe déjà
    
    print(f"Film non trouvé dans la base de données, récupération depuis TMDB...")
    # Si le film n'existe pas, récupérer les données depuis TMDB
    movie_data = get_movie_from_tmdb(movie_id)
    
    if not movie_data:
        print(f"Erreur lors de la récupération du film depuis TMDB.")
        return None, False  # Erreur lors de la récupération des données
    
    # Vérifier que le titre n'est pas null (requis pour la base de données)
    if not movie_data.get("title"):
        print("Le titre du film est manquant.")
        return None, False
    
    print(f"Film récupéré depuis TMDB: {movie_data}")
    
    # Créer un nouveau film dans la base de données
    try:
        new_movie = Movie(
            id=movie_id,  # Utiliser l'ID TMDB comme ID dans notre base
            title=movie_data["title"],
            overview=movie_data["overview"],
            poster_path=movie_data["poster_path"],
            genres=movie_data["genres"],
            popularity=movie_data["popularity"],
            release_date=movie_data["release_date"]
        )
        
        db.session.add(new_movie)
        db.session.commit()
        
        print(f"Nouveau film créé: {new_movie}")
        return new_movie, True  # Nouveau film créé
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la création du film: {e}")
        return None, False
