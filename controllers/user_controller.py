from flask_cors import cross_origin 
from flask import Blueprint, request, jsonify, session, current_app
from models.user import User
from database.db import db
import jwt
import os
import datetime
import firebase_admin
from firebase_admin import credentials, auth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import uuid
from PIL import Image
import io
import json

user_bp = Blueprint('user', __name__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'votre_clef_secrete_par_defaut')
logger = logging.getLogger(__name__)

# Extensions d'images autorisées
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def optimize_image(image_file, max_size=(800, 800), quality=85):
    """Optimise une image en la redimensionnant et compressant"""
    try:
        # Ouvrir l'image
        img = Image.open(image_file)
        
        # Convertir en RGB si nécessaire
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Redimensionner si nécessaire
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Sauvegarder dans un buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation de l'image: {str(e)}")
        return None

def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

@user_bp.route('/<path:path>', methods=['OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def options_handler(path):
    return '', 200

@user_bp.route('/upload-image/<int:id>', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def upload_image(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

    # Vérifier si un fichier a été envoyé
    if 'image' not in request.files:
        return jsonify({'error': 'Aucune image envoyée'}), 400
        
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Type de fichier non autorisé. Utilisez PNG, JPG, JPEG, GIF ou WEBP'}), 400

    # Vérifier la taille du fichier
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'Fichier trop volumineux. Maximum 5MB autorisé'}), 400

    try:
        # Configuration du dossier d'upload
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_folder = os.path.join(base_dir, 'static', 'uploads')
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(upload_folder, exist_ok=True)
        
        logger.info(f"📁 Dossier upload: {upload_folder}")
        logger.info(f"📁 Dossier existe: {os.path.exists(upload_folder)}")
        logger.info(f"📄 Fichier reçu: {file.filename}, Taille: {file_size} bytes")
        
        # Supprimer l'ancienne image si elle existe
        if user.image and user.image.startswith('http://localhost:5000/static/uploads/'):
            old_filename = user.image.split('/')[-1]
            old_file_path = os.path.join(upload_folder, old_filename)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                    logger.info(f"🗑️ Ancienne image supprimée: {old_file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de supprimer l'ancienne image: {str(e)}")
        
        # Générer un nom de fichier unique
        file_extension = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(datetime.datetime.now().timestamp())
        unique_filename = f"user_{user.id}_{timestamp}_{unique_id}.jpg"  # Toujours en JPG après optimisation
        
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Optimiser et sauvegarder l'image
        optimized_image = optimize_image(file)
        if optimized_image:
            with open(file_path, 'wb') as f:
                f.write(optimized_image.getvalue())
            logger.info(f"✅ Image optimisée et sauvegardée: {file_path}")
        else:
            # Fallback: sauvegarder l'image originale
            file.save(file_path)
            logger.info(f"✅ Image originale sauvegardée: {file_path}")
        
        # Vérifier que le fichier a bien été sauvegardé
        if not os.path.exists(file_path):
            return jsonify({'error': 'Erreur lors de la sauvegarde du fichier'}), 500
        
        # Vérifier la taille du fichier sauvegardé
        saved_size = os.path.getsize(file_path)
        logger.info(f"📊 Taille du fichier sauvegardé: {saved_size} bytes")
        
        # Mettre à jour l'URL de l'image dans la base de données
        server_url = request.host_url.rstrip('/')
        image_url = f"{server_url}/static/uploads/{unique_filename}"
        
        user.image = image_url
        db.session.commit()
        
        logger.info(f"✅ URL de l'image sauvegardée: {image_url}")
        
        return jsonify({
            'message': 'Image enregistrée avec succès',
            'image': image_url,
            'filename': unique_filename,
            'original_size': file_size,
            'optimized_size': saved_size,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erreur lors de l'upload de l'image: {str(e)}")
        return jsonify({'error': f'Erreur lors de l\'enregistrement de l\'image: {str(e)}'}), 500

@user_bp.route('/<int:id>', methods=['PUT', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def update_user(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

    data = request.get_json()
    
    if 'fullname' in data:
        user.fullname = data['fullname']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profil mis à jour avec succès',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la mise à jour: {str(e)}'}), 500

@user_bp.route('/signup', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def signup():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
        
    # Vérifier les champs requis
    required_fields = ['fullname', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Le champ {field} est requis'}), 400
    
    # Vérifier si l'email existe déjà
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Cet email est déjà utilisé'}), 409
    
    # Créer un nouvel utilisateur
    try:
        new_user = User(
            fullname=data['fullname'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            firebase_uid=data.get('uid')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Générer un token pour l'utilisateur
        token = generate_token(new_user.id)
        
        # Stocker l'ID utilisateur dans la session
        session['id'] = new_user.id
        
        return jsonify({
            'message': 'Inscription réussie',
            'token': token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de l\'inscription: {str(e)}'}), 500

@user_bp.route('/signin', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def signin():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json()
    
    if 'email' in data and 'password' in data:
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email et mot de passe requis'}), 400
            
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
        if user.password and check_password_hash(user.password, password):
            session['id'] = user.id
            token = generate_token(user.id)
            
            return jsonify({
                'message': 'Connexion réussie',
                'token': token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Mot de passe incorrect'}), 401
    
    elif 'idToken' in data:
        id_token = data.get('idToken')
        if not id_token:
            return jsonify({'error': 'Token manquant'}), 400
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email')
            name = decoded_token.get('name')
            picture = decoded_token.get('picture')
            
            if not email:
                return jsonify({'error': 'Email non disponible'}), 400
                
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    fullname=name or "Utilisateur",
                    email=email,
                    password="",
                    image=picture or ""
                )
                db.session.add(user)
                db.session.commit()
            
            session['id'] = user.id
            token = generate_token(user.id)
                
            return jsonify({
                'message': 'Connexion réussie',
                'token': token,
                'user': user.to_dict()
            }), 200
            
        except firebase_admin.exceptions.FirebaseError as e:
            return jsonify({'error': f'Erreur de vérification Firebase: {str(e)}'}), 401
        except Exception as e:
            return jsonify({'error': f'Erreur interne du serveur: {str(e)}'}), 500
            
    elif 'provider' in data and ('google' in data['provider'] or 'apple' in data['provider']):
        try:
            email = data.get('email')
            if not email:
                return jsonify({'error': 'Email non disponible'}), 400
                
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    fullname=data.get('displayName') or "Utilisateur",
                    email=email,
                    password="",
                    image=data.get('photoURL') or ""
                )
                db.session.add(user)
                db.session.commit()
            
            session['id'] = user.id
            token = generate_token(user.id)
                
            return jsonify({
                'message': 'Connexion réussie',
                'token': token,
                'user': user.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Erreur interne du serveur: {str(e)}'}), 500
    
    else:
        return jsonify({'error': 'Format de données invalide'}), 400

@user_bp.route('/signout', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def signout():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Déconnexion Firebase si utilisé
        id_token = request.json.get('idToken') if request.json else None
        if id_token:
            decoded_token = auth.verify_id_token(id_token)
            auth.revoke_refresh_tokens(decoded_token['sub'])
            
        # Nettoyage complet de la session Flask
        session.clear()
        
        # Réponse avec suppression du cookie de session
        response = jsonify({'message': 'Déconnexion réussie'})
        response.set_cookie('session', '', expires=0)
        return response
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la déconnexion: {str(e)}'}), 500

@user_bp.route('/me', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_current_user():
    if request.method == 'OPTIONS':
        return '', 200
        
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        if 'id' not in session:
            return jsonify({'error': 'Non authentifié'}), 401
        user_id = session['id']
    else:
        token = token.split(' ')[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
    
    user = User.query.get(user_id)
    
    if not user:
        if 'id' in session:
            session.pop('id')
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
    return jsonify({
        'user': user.to_dict()
    }), 200

@user_bp.route('/verify', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def verify_token():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json()
    
    if 'idToken' not in data:
        return jsonify({'error': 'No ID token provided'}), 400
        
    id_token = data.get('idToken')
    
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name', email.split('@')[0] if email else "Utilisateur")
        picture = decoded_token.get('picture')
        
        if not email:
            return jsonify({'error': 'Email non disponible'}), 400
            
        # Find user or create new one
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            user = User(
                fullname=name,
                email=email,
                password="",
                image=picture or "",
                firebase_uid=uid
            )
            db.session.add(user)
            db.session.commit()
        elif not user.firebase_uid:
            # Update existing user with Firebase UID
            user.firebase_uid = uid
            db.session.commit()
        
        # Set session
        session['id'] = user.id
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Vérification réussie',
            'token': token,
            **user.to_dict()
        }), 200
        
    except firebase_admin.exceptions.FirebaseError as e:
        return jsonify({'error': f'Erreur de vérification Firebase: {str(e)}'}), 401
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return jsonify({'error': f'Erreur interne du serveur: {str(e)}'}), 500

@user_bp.route('/<int:id>', methods=['GET', 'PUT', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_user(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    if request.method == 'PUT':
        user = User.query.get(id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        data = request.get_json()
        
        if 'fullname' in data:
            user.fullname = data['fullname']
        
        try:
            db.session.commit()
            return jsonify({
                'message': 'Profil mis à jour avec succès',
                'user': user.to_dict()
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Erreur lors de la mise à jour: {str(e)}'}), 500
    
    elif request.method == 'GET':
        user = User.query.get(id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
        return jsonify(user.to_dict()), 200

# ENDPOINT POUR LES LIKES D'UN UTILISATEUR
@user_bp.route('/<int:user_id>/likes', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_user_likes(user_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        from models.like import Like
        from models.movie import Movie
        
        logger.info(f"🔍 Récupération des likes pour l'utilisateur {user_id}")
        
        # Récupérer tous les likes de l'utilisateur
        likes = db.session.query(Like).filter_by(user_id=user_id).all()
        
        logger.info(f"📊 Nombre de likes trouvés: {len(likes)}")
        
        likes_data = []
        for like in likes:
            like_dict = {
                'id': like.id,
                'user_id': like.user_id,
                'movie_id': like.movie_id,
                'created_at': like.created_at.isoformat() if like.created_at else None
            }
            likes_data.append(like_dict)
        
        logger.info(f"✅ Likes récupérés avec succès pour l'utilisateur {user_id}")
        return jsonify(likes_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des likes: {str(e)}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

# CORRECTION: Endpoint stats avec configuration CORS simplifiée
@user_bp.route('/<int:id>/stats', methods=['GET', 'OPTIONS'])
def get_user_stats(id):
    # CORRECTION: Gestion manuelle des CORS pour éviter les doublons
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 200
        
    user = User.query.get(id)
    if not user:
        response = jsonify({'error': 'Utilisateur non trouvé'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 404
    
    try:
        logger.info(f"🔍 Récupération des statistiques pour l'utilisateur {id}")
        
        # Importer les modèles nécessaires
        from models.movie import Movie
        from models.like import Like
        from models.comment import Comment
        from models.watchlist import Watchlist
        from sqlalchemy import func, desc, text
        
        # STATISTIQUES DE BASE
        logger.info("📊 Calcul des statistiques de base...")
        
        # Nombre de films aimés
        liked_movies_count = db.session.query(func.count(Like.id)).filter(Like.user_id == id).scalar() or 0
        logger.info(f"❤️ Films aimés: {liked_movies_count}")
        
        # Nombre de films dans la watchlist
        watchlist_count = db.session.query(func.count(Watchlist.id)).filter(Watchlist.user_id == id).scalar() or 0
        logger.info(f"📋 Watchlist: {watchlist_count}")
        
        # Nombre de commentaires
        comments_count = db.session.query(func.count(Comment.id)).filter(Comment.user_id == id).scalar() or 0
        logger.info(f"💬 Commentaires: {comments_count}")
        
        # DATE D'INSCRIPTION
        if hasattr(user, 'created_at') and user.created_at:
            member_since = user.created_at.strftime("%B %Y")
            # Traduire les mois en français
            months_fr = {
                'January': 'Janvier', 'February': 'Février', 'March': 'Mars',
                'April': 'Avril', 'May': 'Mai', 'June': 'Juin',
                'July': 'Juillet', 'August': 'Août', 'September': 'Septembre',
                'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'
            }
            for en, fr in months_fr.items():
                member_since = member_since.replace(en, fr)
        else:
            member_since = "Juin 2025"
        
        logger.info(f"📅 Membre depuis: {member_since}")
        
        # ACTIVITÉS RÉCENTES
        logger.info("🔄 Récupération des activités récentes...")
        recent_activities = []
        
        # Récupérer les likes récents avec gestion d'erreur
        try:
            recent_likes = db.session.query(Like, Movie.title).outerjoin(
                Movie, Like.movie_id == Movie.id
            ).filter(
                Like.user_id == id
            ).order_by(
                desc(Like.created_at)
            ).limit(3).all()
            
            logger.info(f"👍 Likes récents trouvés: {len(recent_likes)}")
            
            for like, movie_title in recent_likes:
                if like.created_at:  # Vérifier que la date existe
                    recent_activities.append({
                        'type': 'like',
                        'movieId': like.movie_id,
                        'movieTitle': movie_title or f"Film #{like.movie_id}",
                        'date': like.created_at.isoformat(),
                        'timeAgo': get_time_ago(like.created_at)
                    })
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la récupération des likes récents: {str(e)}")
        
        # Récupérer les ajouts récents à la watchlist avec gestion d'erreur
        try:
            recent_watchlist = db.session.query(Watchlist, Movie.title).outerjoin(
                Movie, Watchlist.movie_id == Movie.id
            ).filter(
                Watchlist.user_id == id
            ).order_by(
                desc(Watchlist.added_at)
            ).limit(3).all()
            
            logger.info(f"📋 Watchlist récente trouvée: {len(recent_watchlist)}")
            
            for watchlist_item, movie_title in recent_watchlist:
                if watchlist_item.added_at:  # Vérifier que la date existe
                    recent_activities.append({
                        'type': 'watchlist',
                        'movieId': watchlist_item.movie_id,
                        'movieTitle': movie_title or f"Film #{watchlist_item.movie_id}",
                        'date': watchlist_item.added_at.isoformat(),
                        'timeAgo': get_time_ago(watchlist_item.added_at)
                    })
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la récupération de la watchlist récente: {str(e)}")
        
        # Récupérer les commentaires récents avec gestion d'erreur
        try:
            recent_comments = db.session.query(Comment, Movie.title).outerjoin(
                Movie, Comment.movie_id == Movie.id
            ).filter(
                Comment.user_id == id
            ).order_by(
                desc(Comment.created_at)
            ).limit(3).all()
            
            logger.info(f"💬 Commentaires récents trouvés: {len(recent_comments)}")
            
            for comment, movie_title in recent_comments:
                if comment.created_at:  # Vérifier que la date existe
                    recent_activities.append({
                        'type': 'comment',
                        'movieId': comment.movie_id,
                        'movieTitle': movie_title or f"Film #{comment.movie_id}",
                        'date': comment.created_at.isoformat(),
                        'timeAgo': get_time_ago(comment.created_at)
                    })
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la récupération des commentaires récents: {str(e)}")
        
        # Trier toutes les activités par date (les plus récentes d'abord)
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        recent_activities = recent_activities[:5]  # Limiter à 5 activités
        
        logger.info(f"🔄 Total activités récentes: {len(recent_activities)}")
        
        # GENRES PRÉFÉRÉS
        logger.info("🎭 Calcul des genres préférés...")
        favorite_genres = get_favorite_genres_from_movie_json(id)
        logger.info(f"🎭 Genres préférés: {favorite_genres}")
        
        # RÉPONSE FINALE
        stats_data = {
            'likedMovies': liked_movies_count,
            'watchlistCount': watchlist_count,
            'commentsCount': comments_count,
            'memberSince': member_since,
            'recentActivities': recent_activities,
            'favoriteGenres': favorite_genres
        }
        
        logger.info(f"✅ Statistiques calculées avec succès pour l'utilisateur {id}")
        logger.info(f"📊 Données finales: {stats_data}")
        
        # CORRECTION: Réponse avec en-têtes CORS manuels
        response = jsonify(stats_data)
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Content-Type'] = 'application/json'
        return response, 200
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des statistiques: {str(e)}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        response = jsonify({'error': f'Erreur interne du serveur: {str(e)}'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 500

def get_time_ago(date):
    """Calcule le temps écoulé depuis une date"""
    try:
        now = datetime.datetime.now()
        
        # S'assurer que date est un objet datetime
        if isinstance(date, str):
            date = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        diff = now - date
        days = diff.days
        
        if days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                if minutes == 0:
                    return "À l'instant"
                return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif days == 1:
            return "Hier"
        elif days < 7:
            return f"Il y a {days} jour{'s' if days > 1 else ''}"
        elif days < 30:
            weeks = days // 7
            return f"Il y a {weeks} semaine{'s' if weeks > 1 else ''}"
        elif days < 365:
            months = days // 30
            return f"Il y a {months} mois"
        else:
            years = days // 365
            return f"Il y a {years} an{'s' if years > 1 else ''}"
    except Exception as e:
        logger.error(f"Erreur dans get_time_ago: {str(e)}")
        return "Date inconnue"

def get_favorite_genres_from_movie_json(user_id):
    """Détermine les genres préférés d'un utilisateur basé sur les genres JSON stockés dans Movie"""
    try:
        from models.movie import Movie
        from models.like import Like
        from models.watchlist import Watchlist
        from collections import Counter
        
        logger.info(f"🎭 Calcul des genres préférés pour l'utilisateur {user_id}")
        
        # Récupérer les genres des films aimés
        liked_movies = db.session.query(Movie.genres).join(
            Like, Like.movie_id == Movie.id
        ).filter(
            Like.user_id == user_id
        ).all()
        
        logger.info(f"❤️ Films aimés avec genres: {len(liked_movies)}")
        
        # Récupérer les genres des films dans la watchlist
        watchlist_movies = db.session.query(Movie.genres).join(
            Watchlist, Watchlist.movie_id == Movie.id
        ).filter(
            Watchlist.user_id == user_id
        ).all()
        
        logger.info(f"📋 Films watchlist avec genres: {len(watchlist_movies)}")
        
        # Compter les genres
        genre_counter = Counter()
        
        # Traiter les films aimés (poids x2)
        for (genres_data,) in liked_movies:
            if genres_data:
                try:
                    if isinstance(genres_data, str):
                        genres = json.loads(genres_data)
                    else:
                        genres = genres_data
                    
                    if isinstance(genres, list):
                        for genre in genres:
                            if isinstance(genre, dict) and 'name' in genre:
                                genre_counter[genre['name']] += 2
                            elif isinstance(genre, str):
                                genre_counter[genre] += 2
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"⚠️ Erreur parsing genres liked: {str(e)}")
                    continue
        
        # Traiter les films de la watchlist (poids x1)
        for (genres_data,) in watchlist_movies:
            if genres_data:
                try:
                    if isinstance(genres_data, str):
                        genres = json.loads(genres_data)
                    else:
                        genres = genres_data
                    
                    if isinstance(genres, list):
                        for genre in genres:
                            if isinstance(genre, dict) and 'name' in genre:
                                genre_counter[genre['name']] += 1
                            elif isinstance(genre, str):
                                genre_counter[genre] += 1
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"⚠️ Erreur parsing genres watchlist: {str(e)}")
                    continue
        
        # Retourner les 4 genres les plus populaires
        most_common_genres = genre_counter.most_common(4)
        favorite_genres = [genre for genre, count in most_common_genres]
        
        logger.info(f"🎭 Genres calculés: {favorite_genres}")
        
        # Si aucun genre trouvé, retourner des genres par défaut
        if not favorite_genres:
            favorite_genres = ["Action", "Aventure", "Science-Fiction", "Thriller"]
            logger.info("🎭 Utilisation des genres par défaut")
        
        return favorite_genres
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des genres préférés: {str(e)}")
        # Retourner des genres par défaut en cas d'erreur
        return ["Action", "Aventure", "Science-Fiction", "Thriller"]
