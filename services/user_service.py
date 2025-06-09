from repositories.user_repository import get_or_create_user

def login_user(decoded_token):
    email = decoded_token.get('email')
    user = get_or_create_user(email)
    return {'message': 'Connecté', 'user': user.to_dict()}
