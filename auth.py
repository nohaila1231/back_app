# Ajouter en haut du fichier
import jwt
import datetime
from functools import wraps

# Clé secrète pour les JWT
SECRET_KEY = "votre_clé_secrète_très_longue_et_aléatoire"

# Fonction pour créer un token JWT
def create_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Décorateur pour vérifier le token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
            
        if not token:
            return jsonify({'error': 'Token manquant'}), 401
            
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['sub']
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
            
        return f(user, *args, **kwargs)
    return decorated