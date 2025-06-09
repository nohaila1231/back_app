from models.notification import Notification
from database.db import db
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

class NotificationRepository:
    """Repository pour les opérations de base de données des notifications"""
    
    @staticmethod
    def create(user_id, sender_id, notification_type, title, message, data=None):
        """Créer une nouvelle notification"""
        try:
            notification = Notification(
                user_id=user_id,
                sender_id=sender_id,
                type=notification_type,
                title=title,
                message=message,
                data=data
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"✅ Notification créée: {notification.id}")
            return notification
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur lors de la création de la notification: {str(e)}")
            return None
    
    @staticmethod
    def get_by_id(notification_id):
        """Récupérer une notification par son ID"""
        try:
            return Notification.query.get(notification_id)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération de la notification {notification_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_by_user(user_id, limit=None, offset=None, unread_only=False):
        """Récupérer les notifications d'un utilisateur"""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(read_status=False)
            
            query = query.order_by(desc(Notification.created_at))
            
            if limit:
                query = query.limit(limit)
            
            if offset:
                query = query.offset(offset)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des notifications pour l'utilisateur {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def count_unread(user_id):
        """Compter les notifications non lues d'un utilisateur"""
        try:
            return Notification.query.filter_by(user_id=user_id, read_status=False).count()
        except Exception as e:
            logger.error(f"❌ Erreur lors du comptage des notifications non lues: {str(e)}")
            return 0
    
    @staticmethod
    def update(notification_id, **kwargs):
        """Mettre à jour une notification"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                for key, value in kwargs.items():
                    if hasattr(notification, key):
                        setattr(notification, key, value)
                
                db.session.commit()
                logger.info(f"✅ Notification {notification_id} mise à jour")
                return notification
            
            return None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur lors de la mise à jour de la notification {notification_id}: {str(e)}")
            return None
    
    @staticmethod
    def delete(notification_id):
        """Supprimer une notification"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                db.session.delete(notification)
                db.session.commit()
                logger.info(f"🗑️ Notification {notification_id} supprimée")
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur lors de la suppression de la notification {notification_id}: {str(e)}")
            return False
    
    @staticmethod
    def mark_all_read(user_id):
        """Marquer toutes les notifications d'un utilisateur comme lues"""
        try:
            updated = Notification.query.filter_by(user_id=user_id, read_status=False).update({'read_status': True})
            db.session.commit()
            logger.info(f"✅ {updated} notifications marquées comme lues")
            return updated
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur lors du marquage en masse: {str(e)}")
            return 0
