from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from models.watchlist import Watchlist
from models.movie import Movie
from models.user import User
from database.db import db
import logging
from datetime import datetime
import json

watchlist_bp = Blueprint('watchlist', __name__)
logger = logging.getLogger(__name__)

# CORRECTION: Cache simple pour éviter les requêtes répétées
watchlist_cache = {}
cache_timeout = 30  # 30 secondes

def get_cached_watchlist(user_id):
    """Récupère la watchlist depuis le cache si disponible"""
    if user_id in watchlist_cache:
        cached_data, timestamp = watchlist_cache[user_id]
        if (datetime.now() - timestamp).seconds < cache_timeout:
            logger.info(f"📋 Returning cached watchlist for user {user_id}")
            return cached_data
    return None

def cache_watchlist(user_id, data):
    """Met en cache la watchlist"""
    watchlist_cache[user_id] = (data, datetime.now())

@watchlist_bp.route('/', methods=['GET', 'POST'])
def manage_watchlist(user_id):
    # Vérifier que l'utilisateur existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    if request.method == 'GET':
        try:
            # CORRECTION: Vérifier le cache d'abord
            cached_data = get_cached_watchlist(user_id)
            if cached_data is not None:
                return jsonify(cached_data), 200
                
            logger.info(f"🔍 Récupération de la watchlist pour l'utilisateur {user_id}")
            
            # Récupérer la watchlist avec les détails des films
            watchlist_items = db.session.query(Watchlist, Movie).join(
                Movie, Watchlist.movie_id == Movie.id, isouter=True
            ).filter(Watchlist.user_id == user_id).order_by(
                Watchlist.added_at.desc()
            ).all()
            
            logger.info(f"📋 Nombre d'éléments dans la watchlist: {len(watchlist_items)}")
            
            watchlist_data = []
            for watchlist_item, movie in watchlist_items:
                if movie:
                    movie_dict = movie.to_dict()
                    movie_dict['added_at'] = watchlist_item.added_at.isoformat() if watchlist_item.added_at else None
                    watchlist_data.append(movie_dict)
                else:
                    # Film non trouvé, créer un objet basique
                    watchlist_data.append({
                        'id': watchlist_item.movie_id,
                        'title': f'Film #{watchlist_item.movie_id}',
                        'overview': 'Description non disponible',
                        'poster_path': '',
                        'popularity': 0.0,
                        'release_date': '2023-01-01',
                        'added_at': watchlist_item.added_at.isoformat() if watchlist_item.added_at else None
                    })
            
            # CORRECTION: Mettre en cache le résultat
            cache_watchlist(user_id, watchlist_data)
            
            logger.info(f"✅ Watchlist récupérée avec succès pour l'utilisateur {user_id}")
            return jsonify(watchlist_data), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération de la watchlist: {str(e)}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Erreur interne: {str(e)}'}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'movie_id' not in data:
                return jsonify({'error': 'ID du film requis'}), 400
            
            movie_id = data['movie_id']
            
            logger.info(f"➕ Ajout du film {movie_id} à la watchlist de l'utilisateur {user_id}")
            
            # Vérifier si le film est déjà dans la watchlist
            existing_item = Watchlist.query.filter_by(
                user_id=user_id, 
                movie_id=movie_id
            ).first()
            
            if existing_item:
                logger.info(f"⚠️ Film {movie_id} déjà dans la watchlist")
                return jsonify({'message': 'Film déjà dans la liste', 'success': True}), 200
            
            # Créer le film s'il n'existe pas
            movie = Movie.query.get(movie_id)
            if not movie:
                logger.info(f"🎬 Création du film {movie_id}")
                
                # Extraire les données du film depuis la requête
                genres_data = data.get('genres', [])
                if isinstance(genres_data, list):
                    genres_json = json.dumps(genres_data)
                else:
                    genres_json = str(genres_data)
                
                movie_data = {
                    'id': movie_id,
                    'title': data.get('title', f'Film #{movie_id}'),
                    'overview': data.get('overview', ''),
                    'poster_path': data.get('poster_path', ''),
                    'popularity': float(data.get('popularity', 0.0)),
                    'release_date': data.get('release_date', '2023-01-01'),
                    'genres': genres_json
                }
                
                movie = Movie(**movie_data)
                db.session.add(movie)
            
            # Ajouter à la watchlist
            new_watchlist_item = Watchlist(
                user_id=user_id,
                movie_id=movie_id,
                added_at=datetime.utcnow()
            )
            
            db.session.add(new_watchlist_item)
            db.session.commit()
            
            # CORRECTION: Invalider le cache après ajout
            if user_id in watchlist_cache:
                del watchlist_cache[user_id]
            
            logger.info(f"✅ Film {movie_id} ajouté à la watchlist avec succès")
            
            # Retourner les données du film ajouté
            movie_dict = movie.to_dict()
            movie_dict['added_at'] = new_watchlist_item.added_at.isoformat()
            
            return jsonify({
                'message': 'Film ajouté à la liste avec succès',
                'success': True,
                'movie': movie_dict
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur lors de l'ajout à la watchlist: {str(e)}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

@watchlist_bp.route('/<int:movie_id>', methods=['DELETE'])
def remove_from_watchlist(user_id, movie_id):
    # Vérifier que l'utilisateur existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    try:
        logger.info(f"🗑️ Suppression du film {movie_id} de la watchlist de l'utilisateur {user_id}")
        
        # Trouver l'élément dans la watchlist
        watchlist_item = Watchlist.query.filter_by(
            user_id=user_id,
            movie_id=movie_id
        ).first()
        
        if not watchlist_item:
            logger.warning(f"⚠️ Film {movie_id} non trouvé dans la watchlist")
            return jsonify({'error': 'Film non trouvé dans la liste'}), 404
        
        # Supprimer de la watchlist
        db.session.delete(watchlist_item)
        db.session.commit()
        
        # CORRECTION: Invalider le cache après suppression
        if user_id in watchlist_cache:
            del watchlist_cache[user_id]
        
        logger.info(f"✅ Film {movie_id} supprimé de la watchlist avec succès")
        return jsonify({'message': 'Film supprimé de la liste avec succès', 'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erreur lors de la suppression de la watchlist: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500
