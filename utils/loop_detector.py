import time
from collections import defaultdict, deque
from flask import request
import threading

# Détecteur de boucles infinies
loop_detector = defaultdict(lambda: defaultdict(deque))
detector_lock = threading.RLock()

def detect_infinite_loop():
    """
    Détecte les boucles infinies en surveillant les patterns de requêtes
    """
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                  request.environ.get('REMOTE_ADDR', 'unknown'))
    endpoint = request.path
    current_time = time.time()
    
    with detector_lock:
        # Ajouter la requête actuelle
        loop_detector[client_ip][endpoint].append(current_time)
        
        # Nettoyer les requêtes anciennes (plus de 2 minutes)
        cutoff_time = current_time - 120
        while (loop_detector[client_ip][endpoint] and 
               loop_detector[client_ip][endpoint][0] < cutoff_time):
            loop_detector[client_ip][endpoint].popleft()
        
        # Détecter les boucles infinies
        recent_requests = len(loop_detector[client_ip][endpoint])
        
        # Seuils d'alerte
        if recent_requests > 100:  # Plus de 100 requêtes en 2 minutes
            print(f"🚨 INFINITE LOOP DETECTED!")
            print(f"   IP: {client_ip}")
            print(f"   Endpoint: {endpoint}")
            print(f"   Requests in last 2 minutes: {recent_requests}")
            print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        elif recent_requests > 50:  # Plus de 50 requêtes en 2 minutes
            print(f"⚠️  High request frequency detected:")
            print(f"   IP: {client_ip}")
            print(f"   Endpoint: {endpoint}")
            print(f"   Requests in last 2 minutes: {recent_requests}")
    
    return False

def apply_loop_detection(app):
    """
    Applique la détection de boucles infinies à l'application Flask
    """
    @app.before_request
    def before_request_loop_detection():
        if request.path.startswith('/api/'):
            is_loop = detect_infinite_loop()
            if is_loop:
                # Log l'incident mais ne bloque pas (pour le debugging)
                print("🔧 Consider implementing temporary IP blocking if this persists")
