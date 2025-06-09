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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
def options_handler(path):
    return '', 200

@user_bp.route('/upload-image/<int:id>', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
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

@user_bp.route('/<int:id>/stats', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app"])
def get_user_stats(id):
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200
        
    # Ajouter des en-têtes CORS à la réponse
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', 'https://client-enqldel1w-louraknouhaila-5950s-projects.vercel.app')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    user = User.query.get(id)
    if not user:
        response = jsonify({'error': 'Utilisateur non trouvé'})
        return add_cors_headers(response), 404
    
    try:
        # Import des modèles CORRECTS
        from models.movie import Movie
        from models.like import Like
        from models.comment import Comment
        from models.watchlist import Watchlist
        from sqlalchemy import func, desc
        
        # Nombre de films aimés
        liked_movies_count = db.session.query(func.count(Like.id)).filter(Like.user_id == id).scalar() or 0
        
        # Nombre de films dans la watchlist
        watchlist_count = db.session.query(func.count(Watchlist.id)).filter(Watchlist.user_id == id).scalar() or 0
        
        # Nombre de commentaires
        comments_count = db.session.query(func.count(Comment.id)).filter(Comment.user_id == id).scalar() or 0
        
        # Date d'inscription (membre depuis)
        member_since = user.created_at.strftime("%B %Y") if hasattr(user, 'created_at') and user.created_at else "Mars 2023"
        
        # Activités récentes
        recent_activities = []
        
        # Récupérer les likes récents
        recent_likes = db.session.query(Like, Movie.title).join(
            Movie, Like.movie_id == Movie.id
        ).filter(
            Like.user_id == id
        ).order_by(
            desc(Like.created_at)
        ).limit(3).all()
        
        for like, movie_title in recent_likes:
            recent_activities.append({
                'type': 'like',
                'movieId': like.movie_id,
                'movieTitle': movie_title,
                'date': like.created_at.isoformat(),
                'timeAgo': get_time_ago(like.created_at)
            })
        
        # Récupérer les ajouts récents à la watchlist - CORRIGÉ: utilise added_at
        recent_watchlist = db.session.query(Watchlist, Movie.title).join(
            Movie, Watchlist.movie_id == Movie.id
        ).filter(
            Watchlist.user_id == id
        ).order_by(
            desc(Watchlist.added_at)  # CORRIGÉ: utilise added_at au lieu de created_at
        ).limit(3).all()
        
        for watchlist_item, movie_title in recent_watchlist:
            recent_activities.append({
                'type': 'watchlist',
                'movieId': watchlist_item.movie_id,
                'movieTitle': movie_title,
                'date': watchlist_item.added_at.isoformat(),  # CORRIGÉ: utilise added_at
                'timeAgo': get_time_ago(watchlist_item.added_at)  # CORRIGÉ: utilise added_at
            })
        
        # Récupérer les commentaires récents
        recent_comments = db.session.query(Comment, Movie.title).join(
            Movie, Comment.movie_id == Movie.id
        ).filter(
            Comment.user_id == id
        ).order_by(
            desc(Comment.created_at)
        ).limit(3).all()
        
        for comment, movie_title in recent_comments:
            recent_activities.append({
                'type': 'comment',
                'movieId': comment.movie_id,
                'movieTitle': movie_title,
                'date': comment.created_at.isoformat(),
                'timeAgo': get_time_ago(comment.created_at)
            })
        
        # Trier toutes les activités par date (les plus récentes d'abord)
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        recent_activities = recent_activities[:5]  # Limiter à 5 activités
        
        # Genres préférés - Version simplifiée qui fonctionne
        favorite_genres = get_favorite_genres_simple(id)
        
        response = jsonify({
            'likedMovies': liked_movies_count,
            'watchlistCount': watchlist_count,
            'commentsCount': comments_count,
            'memberSince': member_since,
            'recentActivities': recent_activities,
            'favoriteGenres': favorite_genres
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        response = jsonify({'error': f'Erreur interne du serveur: {str(e)}'})
        return add_cors_headers(response), 500

def get_time_ago(date):
    """Calcule le temps écoulé depuis une date"""
    now = datetime.datetime.now()
    diff = now - date
    
    days = diff.days
    
    if days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = diff.seconds // 60
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

def get_favorite_genres_simple(user_id):
    """Version simplifiée pour récupérer les genres préférés sans erreur d'import"""
    try:
        from models.movie import Movie
        from models.like import Like  # Import correct depuis models.like
        from models.watchlist import Watchlist
        
        # Récupérer les films aimés et dans la watchlist
        liked_movies = db.session.query(Movie.genres).join(
            Like, Like.movie_id == Movie.id
        ).filter(Like.user_id == user_id).all()
        
        watchlist_movies = db.session.query(Movie.genres).join(
            Watchlist, Watchlist.movie_id == Movie.id
        ).filter(Watchlist.user_id == user_id).all()
        
        # Compter les genres
        genre_counts = {}
        
        # Traiter les films aimés
        for (genres,) in liked_movies:
            if genres:
                if isinstance(genres, str):
                    import json
                    try:
                        genre_list = json.loads(genres)
                    except:
                        continue
                else:
                    genre_list = genres
                
                if isinstance(genre_list, list):
                    for genre in genre_list:
                        if isinstance(genre, dict) and 'name' in genre:
                            genre_name = genre['name']
                        else:
                            genre_name = str(genre)
                        genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 2  # Les likes ont plus de poids
        
        # Traiter les films de la watchlist
        for (genres,) in watchlist_movies:
            if genres:
                if isinstance(genres, str):
                    import json
                    try:
                        genre_list = json.loads(genres)
                    except:
                        continue
                else:
                    genre_list = genres
                
                if isinstance(genre_list, list):
                    for genre in genre_list:
                        if isinstance(genre, dict) and 'name' in genre:
                            genre_name = genre['name']
                        else:
                            genre_name = str(genre)
                        genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1
        
        # Trier par nombre d'occurrences et retourner les top 4
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        return [genre for genre, _ in sorted_genres[:4]]
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des genres préférés: {str(e)}")
        return ["Action", "Aventure", "Science-Fiction", "Thriller"]  # Valeurs par défaut
