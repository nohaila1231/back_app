from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.movie_controller import movie_bp
from controllers.like_controller import like_bp
from controllers.comment_controller import comment_bp
from controllers.watchlist_controller import watchlist_bp
from controllers.recommendation_controller import recommendation_bp
from controllers.notification_controller import notification_bp

def register_routes(app):
    # Routes d'authentification
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Routes utilisateur
    app.register_blueprint(user_bp, url_prefix='/api/users')
    
    # Routes des films
    app.register_blueprint(movie_bp, url_prefix='/api/movies')
    
    # Routes des likes
    # Utilisation des préfixes dynamiques pour inclure l'ID du film dans l'URL
    app.register_blueprint(like_bp, url_prefix='/api/movies')
    
    # Routes des commentaires
    app.register_blueprint(comment_bp, url_prefix='/api/movies')
    
    # Routes de la watchlist
    app.register_blueprint(watchlist_bp, url_prefix='/api/users/<int:user_id>/watchlist')

    # Ajouter une route supplémentaire pour les likes utilisateur avec un nom unique
    app.register_blueprint(like_bp, url_prefix='/api/users', name='user_likes')

    #app.register_blueprint(click_bp, url_prefix='/api/clicks')
    app.register_blueprint(recommendation_bp, url_prefix='/api/recommendations')

     # Routes notifications - AJOUT CRUCIAL
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    
