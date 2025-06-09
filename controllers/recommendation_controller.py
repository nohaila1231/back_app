from flask import Blueprint, request, jsonify
from utils.rate_limiter import rate_limit
from services.recommendation_service import get_recommendations_for_user, train_recommendation_models
import traceback

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/user/<int:user_id>', methods=['GET'])
@rate_limit(max_requests=10, window_seconds=60)  # 10 requêtes par minute
def get_user_recommendations(user_id):
    """Récupérer les recommandations personnalisées pour un utilisateur."""
    try:
        print(f"=== GET RECOMMENDATIONS DEBUG ===")
        print(f"User ID: {user_id}")
        
        limit = request.args.get('limit', 10, type=int)
        print(f"Limit: {limit}")
        
        # Limiter le nombre maximum de recommandations
        if limit > 50:
            limit = 50
        
        # CORRECTION: Utiliser le service de recommandation au lieu de retourner une liste vide
        recommendations = get_recommendations_for_user(user_id, limit)
        
        # Convertir les objets Movie en dictionnaires pour la sérialisation JSON
        recommendations_data = []
        for movie in recommendations:
            movie_dict = {
                'id': movie.id,
                'title': movie.title,
                'overview': movie.overview,
                'poster_path': movie.poster_path,
                'genres': movie.genres,
                'popularity': movie.popularity,
                'release_date': movie.release_date
            }
            recommendations_data.append(movie_dict)
        
        print(f"Returning {len(recommendations_data)} personalized recommendations")
        print(f"Recommended movies: {[movie['title'] for movie in recommendations_data[:5]]}")
        
        return jsonify(recommendations_data)
        
    except Exception as e:
        print(f"=== ERROR IN GET RECOMMENDATIONS ===")
        print(f"Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # En cas d'erreur, retourner une liste vide plutôt qu'une erreur 500
        # Le frontend utilisera alors les films populaires comme fallback
        return jsonify([]), 200

@recommendation_bp.route('/train', methods=['POST'])
@rate_limit(max_requests=1, window_seconds=300)  # 1 requête par 5 minutes
def train_models():
    """Entraîner les modèles de recommandation."""
    try:
        print("=== TRAIN MODELS DEBUG ===")
        
        # CORRECTION: Utiliser la fonction d'entraînement du service
        success = train_recommendation_models()
        
        if success:
            print("Training completed successfully")
            return jsonify({'message': 'Models trained successfully'}), 200
        else:
            print("Training failed")
            return jsonify({'error': 'Training failed'}), 500
        
    except Exception as e:
        print(f"=== ERROR IN TRAIN MODELS ===")
        print(f"Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Erreur lors de l\'entraînement: {str(e)}'}), 500

@recommendation_bp.route('/popular', methods=['GET'])
@rate_limit(max_requests=20, window_seconds=60)  # 20 requêtes par minute pour les films populaires
def get_popular_movies():
    """Récupérer les films populaires (fallback pour les utilisateurs non authentifiés)."""
    try:
        from services.recommendation_service import recommendation_service
        
        limit = request.args.get('limit', 10, type=int)
        if limit > 50:
            limit = 50
        
        # Utiliser la méthode de recommandation par popularité
        popular_movie_ids = recommendation_service.get_popularity_recommendations(limit)
        
        # Récupérer les détails des films
        from models.movie import Movie
        movies = Movie.query.filter(Movie.id.in_(popular_movie_ids)).all()
        
        movies_data = []
        for movie in movies:
            movie_dict = {
                'id': movie.id,
                'title': movie.title,
                'overview': movie.overview,
                'poster_path': movie.poster_path,
                'genres': movie.genres,
                'popularity': movie.popularity,
                'release_date': movie.release_date
            }
            movies_data.append(movie_dict)
        
        return jsonify(movies_data)
        
    except Exception as e:
        print(f"Error getting popular movies: {e}")
        return jsonify([]), 200
