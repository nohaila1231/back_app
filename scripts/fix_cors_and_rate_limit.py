"""
Script pour tester et corriger les problèmes CORS et de rate limiting
"""

import sys
import os
import requests
import time

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_cors_and_endpoints():
    base_url = "http://localhost:5000"
    
    print("🔍 Test de connectivité au serveur Flask...")
    
    try:
        # Test de base
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Serveur Flask accessible")
        else:
            print(f"⚠️ Serveur répond avec le code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur Flask")
        print("💡 Assurez-vous que le serveur est en cours d'exécution avec 'python app.py'")
        return False
    
    print("\n🔍 Test des en-têtes CORS...")
    
    # Test OPTIONS pour CORS
    try:
        headers = {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{base_url}/api/users/1/stats", headers=headers)
        print(f"OPTIONS response: {response.status_code}")
        print(f"CORS headers: {dict(response.headers)}")
        
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✅ En-têtes CORS présents")
        else:
            print("❌ En-têtes CORS manquants")
            
    except Exception as e:
        print(f"❌ Erreur lors du test CORS: {str(e)}")
    
    print("\n🔍 Test du rate limiting...")
    
    # Test de plusieurs requêtes rapides
    try:
        for i in range(5):
            response = requests.get(f"{base_url}/api/test-uploads")
            print(f"Requête {i+1}: {response.status_code}")
            if response.status_code == 429:
                print("⚠️ Rate limiting activé - trop de requêtes")
                break
            time.sleep(0.1)
    except Exception as e:
        print(f"❌ Erreur lors du test de rate limiting: {str(e)}")
    
    return True

def test_user_stats_endpoint():
    print("\n🔍 Test spécifique de l'endpoint /users/{id}/stats...")
    
    try:
        from app import app
        from models.user import User
        
        with app.app_context():
            user = User.query.first()
            if not user:
                print("❌ Aucun utilisateur trouvé")
                return
            
            user_id = user.id
            print(f"✅ Test avec l'utilisateur ID: {user_id}")
        
        # Test de l'endpoint
        url = f"http://localhost:5000/api/users/{user_id}/stats"
        headers = {
            'Origin': 'http://localhost:5173',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Endpoint fonctionne correctement")
            data = response.json()
            print(f"Données reçues: {list(data.keys())}")
        elif response.status_code == 429:
            print("⚠️ Rate limiting - attendez quelques secondes et réessayez")
        elif response.status_code == 404:
            print("❌ Endpoint non trouvé - vérifiez que l'endpoint est correctement défini")
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    print("🔧 Test et diagnostic CORS/Rate Limiting")
    print("=" * 50)
    
    if test_cors_and_endpoints():
        test_user_stats_endpoint()
    
    print("\n💡 Solutions recommandées:")
    print("1. Redémarrez le serveur Flask après avoir appliqué les corrections")
    print("2. Vérifiez que le serveur écoute sur http://localhost:5000")
    print("3. Attendez quelques secondes entre les requêtes pour éviter le rate limiting")
    print("4. Vérifiez les logs du serveur pour plus de détails")
