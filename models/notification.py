from database.db import db
from datetime import datetime
import json

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'comment_reply', 'comment_like', 'movie_like', etc.
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.Text)  # JSON data pour des infos supplémentaires
    read_status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications_received')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='notifications_sent')
    
    def to_dict(self):
        data_dict = {}
        if self.data:
            try:
                data_dict = json.loads(self.data) if isinstance(self.data, str) else self.data
            except (json.JSONDecodeError, TypeError):
                data_dict = {}
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.fullname if self.sender else 'Utilisateur inconnu',
            'sender_avatar': self.sender.image if self.sender else None,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': data_dict,
            'read_status': self.read_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'time_ago': self.get_time_ago()
        }
    
    def get_time_ago(self):
        if not self.created_at:
            return "Date inconnue"
        
        now = datetime.utcnow()
        diff = now - self.created_at
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
    
    @staticmethod
    def create_notification(user_id, sender_id, notification_type, title, message, data=None):
        """Créer une nouvelle notification"""
        try:
            # Éviter les auto-notifications
            if user_id == sender_id:
                return None
            
            notification = Notification(
                user_id=user_id,
                sender_id=sender_id,
                type=notification_type,
                title=title,
                message=message,
                data=json.dumps(data) if data else None
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return notification
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la création de la notification: {str(e)}")
            return None
