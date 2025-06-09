from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from models.comment import Comment
from models.user import User
from models.comment_like import CommentLike
from database.db import db
import logging

# Import des services de notification
from services.notification_service import NotificationService

comment_bp = Blueprint('comment', __name__)
logger = logging.getLogger(__name__)

@comment_bp.route('/<path:path>', methods=['OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def options_handler(path):
    return '', 200

@comment_bp.route('/<int:movie_id>/comments/', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_comments(movie_id):
    """Récupérer tous les commentaires d'un film"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = request.args.get('user_id')
        
        # Récupérer tous les commentaires du film
        comments = Comment.query.filter_by(movie_id=movie_id, parent_id=None).order_by(Comment.created_at.desc()).all()
        
        comments_data = []
        for comment in comments:
            comment_dict = comment.to_dict()
            
            # Ajouter les informations de like si l'utilisateur est connecté
            if user_id:
                like = CommentLike.query.filter_by(comment_id=comment.id, user_id=user_id).first()
                comment_dict['is_liked_by_user'] = like is not None
            else:
                comment_dict['is_liked_by_user'] = False
            
            # Compter les likes
            likes_count = CommentLike.query.filter_by(comment_id=comment.id).count()
            comment_dict['likes_count'] = likes_count
            
            # Récupérer les réponses
            replies = Comment.query.filter_by(parent_id=comment.id).order_by(Comment.created_at.asc()).all()
            replies_data = []
            
            for reply in replies:
                reply_dict = reply.to_dict()
                
                # Ajouter les informations de like pour les réponses
                if user_id:
                    reply_like = CommentLike.query.filter_by(comment_id=reply.id, user_id=user_id).first()
                    reply_dict['is_liked_by_user'] = reply_like is not None
                else:
                    reply_dict['is_liked_by_user'] = False
                
                # Compter les likes des réponses
                reply_likes_count = CommentLike.query.filter_by(comment_id=reply.id).count()
                reply_dict['likes_count'] = reply_likes_count
                
                replies_data.append(reply_dict)
            
            comment_dict['replies'] = replies_data
            comments_data.append(comment_dict)
        
        return jsonify(comments_data), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commentaires: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@comment_bp.route('/<int:movie_id>/comments/', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def add_comment(movie_id):
    """Ajouter un nouveau commentaire"""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    user_id = data.get('user_id')
    content = data.get('content')
    parent_id = data.get('parent_id')  # Pour les réponses
    
    if not user_id or not content:
        return jsonify({'error': 'Données manquantes'}), 400
    
    try:
        # Créer le nouveau commentaire
        new_comment = Comment(
            movie_id=movie_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id
        )
        
        db.session.add(new_comment)
        db.session.commit()
        
        # NOUVEAU: Créer une notification pour les réponses
        if parent_id:
            parent_comment = Comment.query.get(parent_id)
            replier_user = User.query.get(user_id)
            
            if parent_comment and replier_user:
                logger.info(f"🔔 Création d'une notification de réponse: {replier_user.fullname} a répondu à {parent_comment.user.fullname}")
                NotificationService.create_comment_reply_notification(parent_comment, new_comment, replier_user)
        
        return jsonify({
            'message': 'Commentaire ajouté avec succès',
            'comment': new_comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'ajout du commentaire: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@comment_bp.route('/<int:movie_id>/comments/<int:comment_id>/like', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def like_comment(movie_id, comment_id):
    """Liker/unliker un commentaire"""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'ID utilisateur requis'}), 400
    
    try:
        # Vérifier si le like existe déjà
        existing_like = CommentLike.query.filter_by(
            comment_id=comment_id, 
            user_id=user_id
        ).first()
        
        comment = Comment.query.get_or_404(comment_id)
        liker_user = User.query.get(user_id)
        
        if existing_like:
            # Unlike
            db.session.delete(existing_like)
            is_liked = False
            logger.info(f"👎 {liker_user.fullname} a retiré son like du commentaire {comment_id}")
        else:
            # Like
            new_like = CommentLike(comment_id=comment_id, user_id=user_id)
            db.session.add(new_like)
            is_liked = True
            
            # NOUVEAU: Créer une notification de like
            if comment and liker_user:
                logger.info(f"🔔 Création d'une notification de like: {liker_user.fullname} a aimé le commentaire de {comment.user.fullname}")
                NotificationService.create_comment_like_notification(comment, liker_user)
        
        db.session.commit()
        
        # Compter les likes
        likes_count = CommentLike.query.filter_by(comment_id=comment_id).count()
        
        return jsonify({
            'is_liked': is_liked,
            'likes_count': likes_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du like du commentaire: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@comment_bp.route('/<int:movie_id>/comments/<int:comment_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def manage_comment(movie_id, comment_id):
    """Modifier ou supprimer un commentaire"""
    if request.method == 'OPTIONS':
        return '', 200
    
    comment = Comment.query.get_or_404(comment_id)
    
    if request.method == 'PUT':
        # Modifier le commentaire
        data = request.get_json()
        user_id = data.get('user_id')
        content = data.get('content')
        
        if not user_id or not content:
            return jsonify({'error': 'Données manquantes'}), 400
        
        if comment.user_id != user_id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        try:
            comment.content = content
            db.session.commit()
            
            return jsonify({
                'message': 'Commentaire modifié avec succès',
                'comment': comment.to_dict()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur lors de la modification du commentaire: {str(e)}")
            return jsonify({'error': 'Erreur interne du serveur'}), 500
    
    elif request.method == 'DELETE':
        # Supprimer le commentaire
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'ID utilisateur requis'}), 400
        
        if comment.user_id != user_id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        try:
            # Supprimer d'abord les likes associés
            CommentLike.query.filter_by(comment_id=comment_id).delete()
            
            # Supprimer les réponses
            Comment.query.filter_by(parent_id=comment_id).delete()
            
            # Supprimer le commentaire
            db.session.delete(comment)
            db.session.commit()
            
            return jsonify({'message': 'Commentaire supprimé avec succès'}), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur lors de la suppression du commentaire: {str(e)}")
            return jsonify({'error': 'Erreur interne du serveur'}), 500
