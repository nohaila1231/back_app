from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.notification_service import NotificationService
from repositories.notification_repository import NotificationRepository
import logging

notification_bp = Blueprint('notification', __name__)
logger = logging.getLogger(__name__)

@notification_bp.route('/<path:path>', methods=['OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def options_handler(path):
    return '', 200

@notification_bp.route('/user/<int:user_id>', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_user_notifications(user_id):
    """Récupérer toutes les notifications d'un utilisateur"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        logger.info(f"🔔 Récupération des notifications pour l'utilisateur {user_id}")
        
        result = NotificationService.get_user_notifications(user_id, page, per_page, unread_only)
        
        if result:
            logger.info(f"✅ {len(result['notifications'])} notifications récupérées")
            return jsonify(result), 200
        else:
            logger.error(f"❌ Erreur lors de la récupération des notifications")
            return jsonify({'error': 'Erreur lors de la récupération des notifications'}), 500
        
    except Exception as e:
        logger.error(f"❌ Erreur dans get_user_notifications: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@notification_bp.route('/user/<int:user_id>/unread-count', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def get_unread_count(user_id):
    """Récupérer le nombre de notifications non lues"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"🔢 Comptage des notifications non lues pour l'utilisateur {user_id}")
        
        count = NotificationService.get_unread_count(user_id)
        
        logger.info(f"✅ {count} notifications non lues trouvées")
        return jsonify({'unread_count': count}), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du comptage des notifications: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@notification_bp.route('/<int:notification_id>/mark-read', methods=['PUT', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def mark_notification_read(notification_id):
    """Marquer une notification comme lue"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"✅ Marquage de la notification {notification_id} comme lue")
        
        success = NotificationService.mark_as_read(notification_id)
        
        if success:
            return jsonify({'message': 'Notification marquée comme lue'}), 200
        else:
            return jsonify({'error': 'Notification non trouvée'}), 404
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du marquage de la notification: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@notification_bp.route('/user/<int:user_id>/mark-all-read', methods=['PUT', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def mark_all_notifications_read(user_id):
    """Marquer toutes les notifications comme lues"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"✅ Marquage de toutes les notifications comme lues pour l'utilisateur {user_id}")
        
        updated = NotificationService.mark_all_as_read(user_id)
        
        return jsonify({
            'message': f'{updated} notifications marquées comme lues'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du marquage des notifications: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@notification_bp.route('/<int:notification_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:5173"])
def delete_notification(notification_id):
    """Supprimer une notification"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"🗑️ Suppression de la notification {notification_id}")
        
        success = NotificationService.delete_notification(notification_id)
        
        if success:
            return jsonify({'message': 'Notification supprimée'}), 200
        else:
            return jsonify({'error': 'Notification non trouvée'}), 404
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression de la notification: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

# Fonctions utilitaires pour créer des notifications (utilisées par d'autres contrôleurs)
def create_comment_like_notification(comment, liker_user):
    """Fonction utilitaire pour créer une notification de like"""
    return NotificationService.create_comment_like_notification(comment, liker_user)

def create_comment_reply_notification(parent_comment, reply_comment, replier_user):
    """Fonction utilitaire pour créer une notification de réponse"""
    return NotificationService.create_comment_reply_notification(parent_comment, reply_comment, replier_user)
