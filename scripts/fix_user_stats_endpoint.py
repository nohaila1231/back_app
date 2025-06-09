"""
Script pour corriger et tester l'endpoint des statistiques utilisateur
"""

import sys
import os
import requests
import json

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_user_stats_endpoint():
    print("🧪 TEST DE L'ENDPOINT /users/{id}/stats")
    print("=" * 50)
    
    try:
        from app import app
        from models.user import User
        
        with app.app_context():
            # Trouver un utilisateur pour le test
            users = User.query.all()
            if not users:
                print("❌ Aucun utilisateur trouvé dans la base de données")
                return
            
            test_user = users[0]
            print(f"🎯 Test avec l'utilisateur ID {test_user.id}: {test_user.fullname}")
        
        # Tester l'endpoint
        base_url = "http://localhost:5000"
        endpoint = f"{base_url}/api/users/{test_user.id}/stats"
        
        print(f"🔍 Test de l'endpoint: {endpoint}")
        
        try:
            response = requests.get(endpoint, timeout=10)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📋 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Endpoint fonctionne!")
                data = response.json()
                print("📄 Données reçues:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            elif response.status_code == 500:
                print("❌ Erreur serveur 500")
                print(f"Réponse: {response.text}")
                print("\n💡 L'erreur est probablement due aux modèles manquants")
            elif response.status_code == 429:
                print("⚠️ Rate limiting - trop de requêtes")
            else:
                print(f"❌ Erreur {response.status_code}")
                print(f"Réponse: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de se connecter au serveur Flask")
            print("💡 Assurez-vous que le serveur est en cours d'exécution")
            return False
        except requests.exceptions.Timeout:
            print("❌ Timeout de la requête")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_user_stats_endpoint()
