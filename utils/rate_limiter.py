from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict, deque
import threading

# Dictionnaire pour stocker les timestamps des requêtes par IP et endpoint
request_history = defaultdict(lambda: defaultdict(deque))
lock = threading.RLock()

def rate_limit(max_requests=60, window_seconds=60, per_endpoint=True):
    """
    Décorateur pour limiter le taux de requêtes
    max_requests: nombre maximum de requêtes autorisées
    window_seconds: fenêtre de temps en secondes
    per_endpoint: si True, limite par endpoint, sinon par IP globalement
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtenir l'IP du client
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
            
            # Obtenir l'endpoint (route)
            endpoint = request.path if per_endpoint else 'global'
            
            current_time = time.time()
            
            with lock:
                # Nettoyer les anciennes requêtes
                while (request_history[client_ip][endpoint] and 
                       request_history[client_ip][endpoint][0] < current_time - window_seconds):
                    request_history[client_ip][endpoint].popleft()
                
                # Vérifier si la limite est dépassée
                if len(request_history[client_ip][endpoint]) >= max_requests:
                    # Calculer le temps restant avant de pouvoir faire une nouvelle requête
                    oldest_request = request_history[client_ip][endpoint][0]
                    reset_time = oldest_request + window_seconds
                    seconds_remaining = int(reset_time - current_time) + 1
                    
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_requests} requests per {window_seconds} seconds',
                        'retry_after': seconds_remaining
                    }), 429, {'Retry-After': str(seconds_remaining)}
                
                # Ajouter la requête actuelle
                request_history[client_ip][endpoint].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Fonction pour appliquer le rate limiting global
def apply_global_rate_limiting(app, max_requests_per_minute=30):
    """
    Applique le rate limiting global à toutes les routes API
    """
    @app.before_request
    def before_request():
        # Appliquer le rate limiting seulement aux routes API
        if request.path.startswith('/api/'):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                          request.environ.get('REMOTE_ADDR', 'unknown'))
            endpoint = request.path
            current_time = time.time()
            
            with lock:
                # Nettoyer les requêtes anciennes (plus d'1 minute)
                while (request_history[client_ip][endpoint] and 
                       request_history[client_ip][endpoint][0] < current_time - 60):
                    request_history[client_ip][endpoint].popleft()
                
                # Limites spéciales pour certains endpoints
                max_requests = max_requests_per_minute
                
                # Plus strict pour les endpoints qui causent des boucles
                if any(pattern in request.path for pattern in ['/watchlist/', '/likes', '/users/']):
                    max_requests = 15  # Très strict pour ces endpoints
                
                if len(request_history[client_ip][endpoint]) >= max_requests:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_requests} requests per minute for this endpoint',
                        'retry_after': 60,
                        'endpoint': endpoint
                    }), 429
                
                # Ajouter la requête actuelle
                request_history[client_ip][endpoint].append(current_time)
