from flask import Blueprint, request, jsonify
from services.user_service import login_user
from security.firebase_utils import verify_firebase_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    id_token = request.json.get('idToken')
    decoded = verify_firebase_token(id_token)
    if decoded:
        return jsonify(login_user(decoded))
    return jsonify({'error': 'Token invalide'}), 401
