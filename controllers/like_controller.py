from flask import Blueprint, request, jsonify, session
from flask_cors import cross_origin
from models.like import Like
from models.movie import Movie
from models.user import User
from database.db import db
import logging

like_bp = Blueprint('like', __name__)
logger = logging.getLogger(__name__)

@like_bp.route('/<int:movie_id>/likes', methods=['POST', 'DELETE', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
def handle_movie_likes(movie_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json() if request.method == 'POST' else request.get_json()
    user_id = data.get('user_id') if data else None
    
    if not user_id:
        return jsonify({'error': 'ID utilisateur requis'}), 400
    
    try:
        if request.method == 'POST':
            # Ajouter un like
            existing_like = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
            if existing_like:
                return jsonify({'message': 'Film déjà aimé'}), 200
            
            # Créer le film s'il n'existe pas
            movie = Movie.query.get(movie_id)
            if not movie:
                movie = Movie(id=movie_id, title="Film inconnu")
                db.session.add(movie)
            
            new_like = Like(user_id=user_id, movie_id=movie_id)
            db.session.add(new_like)
            db.session.commit()
            
            return jsonify({'message': 'Film aimé avec succès'}), 201
            
        elif request.method == 'DELETE':
            # Supprimer un like
            like = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
            if not like:
                return jsonify({'error': 'Like non trouvé'}), 404
            
            db.session.delete(like)
            db.session.commit()
            
            return jsonify({'message': 'Like supprimé avec succès'}), 200
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la gestion du like: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

# NOUVEAU: Endpoint spécifique pour récupérer les likes d'un utilisateur
@like_bp.route('/<int:user_id>/likes', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
def get_user_likes(user_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"🔍 Récupération des likes pour l'utilisateur {user_id}")
        
        # Récupérer tous les likes de l'utilisateur avec les détails du film
        likes = db.session.query(Like, Movie).join(
            Movie, Like.movie_id == Movie.id, isouter=True
        ).filter(Like.user_id == user_id).all()
        
        logger.info(f"📊 Nombre de likes trouvés: {len(likes)}")
        
        likes_data = []
        for like, movie in likes:
            like_dict = {
                'id': like.id,
                'user_id': like.user_id,
                'movie_id': like.movie_id,
                'created_at': like.created_at.isoformat() if like.created_at else None
            }
            
            if movie:
                like_dict['movie'] = movie.to_dict()
            
            likes_data.append(like_dict)
        
        logger.info(f"✅ Likes récupérés avec succès pour l'utilisateur {user_id}")
        return jsonify(likes_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des likes: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

@like_bp.route('/<int:movie_id>/likes/count', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
def get_movie_likes_count(movie_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        count = Like.query.filter_by(movie_id=movie_id).count()
        return jsonify({'count': count}), 200
    except Exception as e:
        logger.error(f"Erreur lors du comptage des likes: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500
