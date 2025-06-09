from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.movie_service import get_movies, get_movie, add_movie, edit_movie, remove_movie, get_or_create_movie
from database.db import db

movie_bp = Blueprint('movie', __name__)

@movie_bp.route('/', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_all_movies():
    if request.method == 'OPTIONS':
        return '', 200
    movies = get_movies()
    return jsonify([movie.to_dict() for movie in movies])

@movie_bp.route('/<int:id>', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_single_movie(id):
    if request.method == 'OPTIONS':
        return '', 200
    movie = get_movie(id)
    if movie:
        return jsonify(movie.to_dict())
    return jsonify({'error': 'Film non trouvé'}), 404

@movie_bp.route('/', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def create_movie():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json()
    movie = add_movie(
        title=data.get('title'),
        overview=data.get('overview'),
        poster_path=data.get('poster_path'),
        genres=data.get('genres'),
        popularity=data.get('popularity'),
        release_date=data.get('release_date')
    )
    if movie:
        return jsonify(movie.to_dict()), 201
    return jsonify({'error': 'Erreur lors de la création'}), 400

@movie_bp.route('/check-or-create', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def check_or_create_movie():
    if request.method == 'OPTIONS':
        return '', 200
    """
    Vérifie si un film existe, ou le crée s'il n'existe pas.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
        
    movie = get_or_create_movie(data['id'])
    if movie:
        return jsonify(movie.to_dict()), 200
    return jsonify({'error': 'Erreur lors de la vérification ou création du film'}), 500

@movie_bp.route('/<int:id>', methods=['PUT', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def update_movie(id):
    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json()
    movie = edit_movie(
        movie_id=id,
        title=data.get('title'),
        overview=data.get('overview'),
        poster_path=data.get('poster_path'),
        genres=data.get('genres'),
        popularity=data.get('popularity'),
        release_date=data.get('release_date')
    )
    if movie:
        return jsonify(movie.to_dict())
    return jsonify({'error': 'Film non trouvé'}), 404

@movie_bp.route('/<int:id>', methods=['DELETE', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def delete_movie(id):
    if request.method == 'OPTIONS':
        return '', 200
    movie = remove_movie(id)
    if movie:
        return jsonify({'message': 'Film supprimé'})
    return jsonify({'error': 'Film non trouvé'}), 404

# Ajout de la route pour enregistrer les clics
@movie_bp.route('/<int:movie_id>/clicks', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def record_click(movie_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'ID utilisateur manquant'}), 400
        
    try:
        # Ici, vous pouvez implémenter la logique pour enregistrer le clic
        # Par exemple, créer une entrée dans une table de clics
        # Pour l'instant, nous retournons simplement un succès
        
        return jsonify({
            'message': 'Clic enregistré avec succès',
            'movie_id': movie_id,
            'user_id': user_id
        }), 200
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'enregistrement du clic: {str(e)}'}), 500
