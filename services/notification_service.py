from models.notification import Notification
from models.user import User
from models.comment import Comment
from database.db import db
import logging
import json

logger = logging.getLogger(__name__)

class NotificationService:
    """Service pour gérer toutes les opérations liées aux notifications"""
    
    @staticmethod
    def create_comment_like_notification(comment, liker_user):
        """Créer une notification pour un like de commentaire"""
        try:
            # Éviter les auto-notifications
            if comment.user_id == liker_user.id:
                logger.info(f"🚫 Auto-notification évitée: {liker_user.fullname} a liké son propre commentaire")
                return None
            
            # Vérifier si une notification similaire existe déjà (éviter le spam)
            existing = Notification.query.filter_by(
                user_id=comment.user_id,
                sender_id=liker_user.id,
                type='comment_like',
                data=json.dumps({
                    'comment_id': comment.id,
                    'movie_id': comment.movie_id
                })
            ).first()
            
            if existing:
                logger.info(f"🔄 Notification de like déjà existante, mise à jour de la date")
                existing.created_at = db.func.now()
                existing.read_status = False
                db.session.commit()
                return existing
            
            # Récupérer le titre du film si possible
            movie_title = f"Film #{comment.movie_id}"
            try:
                from models.movie import Movie
                movie = Movie.query.get(comment.movie_id)
                if movie and movie.title:
                    movie_title = movie.title
            except Exception as e:
                logger.warning(f"⚠️ Impossible de récupérer le titre du film: {str(e)}")
            
            data = {
                'comment_id': comment.id,
                'movie_id': comment.movie_id,
                'movie_title': movie_title
            }
            
            notification = Notification.create_notification(
                user_id=comment.user_id,
                sender_id=liker_user.id,
                notification_type='comment_like',
                title='Nouveau like sur votre commentaire',
                message=f'{liker_user.fullname} a aimé votre commentaire',
                data=data
            )
            
            if notification:
                logger.info(f"✅ Notification de like créée: {liker_user.fullname} -> {comment.user.fullname}")
                return notification
            else:
                logger.error(f"❌ Échec de création de notification de like")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la notification de like: {str(e)}")
            return None
    
    @staticmethod
    def create_comment_reply_notification(parent_comment, reply_comment, replier_user):
        """Créer une notification pour une réponse à un commentaire"""
        try:
            # Éviter les auto-notifications
            if parent_comment.user_id == replier_user.id:
                logger.info(f"🚫 Auto-notification évitée: {replier_user.fullname} a répondu à son propre commentaire")
                return None
            
            # Récupérer le titre du film si possible
            movie_title = f"Film #{reply_comment.movie_id}"
            try:
                from models.movie import Movie
                movie = Movie.query.get(reply_comment.movie_id)
                if movie and movie.title:
                    movie_title = movie.title
            except Exception as e:
                logger.warning(f"⚠️ Impossible de récupérer le titre du film: {str(e)}")
            
            data = {
                'comment_id': reply_comment.id,
                'parent_comment_id': parent_comment.id,
                'movie_id': reply_comment.movie_id,
                'movie_title': movie_title
            }
            
            notification = Notification.create_notification(
                user_id=parent_comment.user_id,
                sender_id=replier_user.id,
                notification_type='comment_reply',
                title='Nouvelle réponse à votre commentaire',
                message=f'{replier_user.fullname} a répondu à votre commentaire',
                data=data
            )
            
            if notification:
                logger.info(f"✅ Notification de réponse créée: {replier_user.fullname} -> {parent_comment.user.fullname}")
                return notification
            else:
                logger.error(f"❌ Échec de création de notification de réponse")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la notification de réponse: {str(e)}")
            return None
    
    @staticmethod
    def get_user_notifications(user_id, page=1, per_page=20, unread_only=False):
        """Récupérer les notifications d'un utilisateur avec pagination"""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(read_status=False)
            
            notifications = query.order_by(Notification.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'notifications': [notif.to_dict() for notif in notifications.items],
                'total': notifications.total,
                'pages': notifications.pages,
                'current_page': page,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des notifications: {str(e)}")
            return None
    
    @staticmethod
    def get_unread_count(user_id):
        """Récupérer le nombre de notifications non lues"""
        try:
            count = Notification.query.filter_by(user_id=user_id, read_status=False).count()
            return count
        except Exception as e:
            logger.error(f"❌ Erreur lors du comptage des notifications: {str(e)}")
            return 0
    
    @staticmethod
    def mark_as_read(notification_id):
        """Marquer une notification comme lue"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                notification.read_status = True
                db.session.commit()
                logger.info(f"✅ Notification {notification_id} marquée comme lue")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors du marquage de la notification: {str(e)}")
            return False
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Marquer toutes les notifications d'un utilisateur comme lues"""
        try:
            updated = Notification.query.filter_by(user_id=user_id, read_status=False).update({'read_status': True})
            db.session.commit()
            logger.info(f"✅ {updated} notifications marquées comme lues pour l'utilisateur {user_id}")
            return updated
        except Exception as e:
            logger.error(f"❌ Erreur lors du marquage des notifications: {str(e)}")
            return 0
    
    @staticmethod
    def delete_notification(notification_id):
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
            logger.error(f"❌ Erreur lors de la suppression de la notification: {str(e)}")
            return False
