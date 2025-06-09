from functools import wraps
from flask import request, jsonify, g
import time
from collections import defaultdict, deque
import threading

# Dictionnaire global pour stocker les requêtes par IP
request_tracker = defaultdict(lambda: defaultdict(deque))
lock = threading.RLock()

def rate_limit_middleware(max_requests_per_minute=60):
    """
    Middleware Flask pour limiter les requêtes par IP
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                          request.environ.get('REMOTE_ADDR', 'unknown'))
            endpoint = request.endpoint or 'unknown'
            current_time = time.time()
            
            with lock:
                # Nettoyer les requêtes anciennes (plus d'1 minute)
                while (request_tracker[client_ip][endpoint] and 
                       request_tracker[client_ip][endpoint][0] < current_time - 60):
                    request_tracker[client_ip][endpoint].popleft()
                
                # Vérifier la limite
                if len(request_tracker[client_ip][endpoint]) >= max_requests_per_minute:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_requests_per_minute} requests per minute',
                        'retry_after': 60
                    }), 429
                
                # Ajouter la requête actuelle
                request_tracker[client_ip][endpoint].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def apply_rate_limiting(app):
    """
    Applique le rate limiting à toutes les routes de l'application
    """
    @app.before_request
    def before_request():
        # Appliquer le rate limiting seulement aux routes API
        if request.path.startswith('/api/'):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                          request.environ.get('REMOTE_ADDR', 'unknown'))
            endpoint = request.endpoint or request.path
            current_time = time.time()
            
            with lock:
                # Nettoyer les requêtes anciennes
                while (request_tracker[client_ip][endpoint] and 
                       request_tracker[client_ip][endpoint][0] < current_time - 60):
                    request_tracker[client_ip][endpoint].popleft()
                
                # Vérifier la limite (plus stricte pour certains endpoints)
                max_requests = 30  # 30 requêtes par minute par défaut
                
                # Limites spéciales pour certains endpoints
                if any(pattern in request.path for pattern in ['/watchlist/', '/likes', '/users/']):
                    max_requests = 20  # Plus strict pour ces endpoints
                
                if len(request_tracker[client_ip][endpoint]) >= max_requests:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_requests} requests per minute for this endpoint',
                        'retry_after': 60
                    }), 429
                
                # Ajouter la requête actuelle
                request_tracker[client_ip][endpoint].append(current_time)
