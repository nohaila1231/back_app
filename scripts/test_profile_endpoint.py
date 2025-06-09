"""
Script pour tester l'endpoint de profil et vérifier que les données sont correctement affichées
"""

import sys
import os
import requests
import json

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Importer la configuration de la base de données
    from app import app
    from database.db import db
    from models.user import User
    
    print("✅ Application Flask importée avec succès")
    
    # Récupérer un utilisateur pour le test
    with app.app_context():
        user = User.query.first()
        if not user:
            print("❌ Aucun utilisateur trouvé dans la base de données")
            sys.exit(1)
        
        user_id = user.id
        print(f"✅ Utilisateur trouvé pour le test:")
        print(f"   - ID: {user_id}")
        print(f"   - Email: {user.email}")
        print(f"   - Nom: {user.fullname}")
        print(f"   - Date de création: {user.created_at if hasattr(user, 'created_at') else 'Non définie'}")
    
    # Tester l'endpoint des statistiques utilisateur
    base_url = "http://localhost:5000/api"
    stats_endpoint = f"{base_url}/users/{user_id}/stats"
    
    print(f"\n🔍 Test de l'endpoint des statistiques: {stats_endpoint}")
    
    try:
        response = requests.get(stats_endpoint, timeout=10)
        
        if response.status_code == 200:
            print("✅ Endpoint des statistiques fonctionnel!")
            data = response.json()
            print("📊 Données reçues:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Vérifier les champs attendus
            expected_fields = ['likedMovies', 'watchlistCount', 'commentsCount', 'memberSince', 'recentActivities', 'favoriteGenres']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                print(f"⚠️ Attention: Champs manquants dans la réponse: {', '.join(missing_fields)}")
            else:
                print("✅ Tous les champs attendus sont présents dans la réponse")
                
        else:
            print(f"❌ Erreur: L'endpoint a retourné le code {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur Flask")
        print("💡 Assurez-vous que le serveur Flask est en cours d'exécution sur http://localhost:5000")
        
    except requests.exceptions.Timeout:
        print("❌ Erreur: Timeout lors de la requête")
        
    # Tester l'endpoint de récupération des données utilisateur
    user_endpoint = f"{base_url}/users/{user_id}"
    
    print(f"\n🔍 Test de l'endpoint utilisateur: {user_endpoint}")
    
    try:
        response = requests.get(user_endpoint, timeout=10)
        
        if response.status_code == 200:
            print("✅ Endpoint utilisateur fonctionnel!")
            data = response.json()
            print("👤 Données utilisateur:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Vérifier si created_at est présent
            if 'created_at' in data:
                print("✅ Le champ 'created_at' est présent dans les données utilisateur")
            else:
                print("⚠️ Le champ 'created_at' n'est pas présent dans les données utilisateur")
                
        else:
            print(f"❌ Erreur: L'endpoint a retourné le code {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au serveur Flask")
        
    except requests.exceptions.Timeout:
        print("❌ Erreur: Timeout lors de la requête")
        
    print("\n✅ Tests terminés")
    
except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()
