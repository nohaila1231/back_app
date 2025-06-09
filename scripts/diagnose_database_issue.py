"""
Script de diagnostic spécifique pour le problème des statistiques de profil
"""

import sys
import os
import requests
import json

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_profile_stats_issue():
    print("🔍 DIAGNOSTIC DU PROBLÈME DES STATISTIQUES DE PROFIL")
    print("=" * 60)
    
    try:
        from app import app
        from models.user import User
        from database.db import db
        from sqlalchemy import text
        
        with app.app_context():
            # 1. Trouver l'utilisateur 38 qui a des données
            user = User.query.get(38)
            if not user:
                print("❌ Utilisateur ID 38 non trouvé")
                users = User.query.all()
                if users:
                    user = users[0]
                    print(f"🎯 Utilisation de l'utilisateur ID {user.id}: {user.fullname}")
                else:
                    print("❌ Aucun utilisateur trouvé")
                    return
            else:
                print(f"✅ Utilisateur ID 38 trouvé: {user.fullname}")
            
            user_id = user.id
            
            # 2. Vérifier les données directement dans la base
            print(f"\n📊 VÉRIFICATION DIRECTE DES DONNÉES POUR L'UTILISATEUR {user_id}:")
            
            # Vérifier les likes
            try:
                with db.engine.connect() as connection:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM likes WHERE user_id = {user_id}"))
                    likes_count = result.scalar()
                    print(f"✅ Likes dans la DB: {likes_count}")
                    
                    if likes_count > 0:
                        result = connection.execute(text(f"SELECT movie_id, added_at FROM likes WHERE user_id = {user_id} LIMIT 3"))
                        likes = result.fetchall()
                        print("   Exemples de likes:")
                        for like in likes:
                            print(f"   - Film ID: {like[0]}, Date: {like[1]}")
            except Exception as e:
                print(f"❌ Erreur lors de la vérification des likes: {str(e)}")
            
            # Vérifier la watchlist
            try:
                with db.engine.connect() as connection:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM watchlists WHERE user_id = {user_id}"))
                    watchlist_count = result.scalar()
                    print(f"✅ Watchlist dans la DB: {watchlist_count}")
                    
                    if watchlist_count > 0:
                        result = connection.execute(text(f"SELECT movie_id, added_at FROM watchlists WHERE user_id = {user_id} LIMIT 3"))
                        watchlist_items = result.fetchall()
                        print("   Exemples de watchlist:")
                        for item in watchlist_items:
                            print(f"   - Film ID: {item[0]}, Date: {item[1]}")
            except Exception as e:
                print(f"❌ Erreur lors de la vérification de la watchlist: {str(e)}")
            
            # Vérifier les commentaires
            try:
                with db.engine.connect() as connection:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM comments WHERE user_id = {user_id}"))
                    comments_count = result.scalar()
                    print(f"✅ Commentaires dans la DB: {comments_count}")
                    
                    if comments_count > 0:
                        result = connection.execute(text(f"SELECT movie_id, content, created_at FROM comments WHERE user_id = {user_id} LIMIT 3"))
                        comments = result.fetchall()
                        print("   Exemples de commentaires:")
                        for comment in comments:
                            content = comment[1][:50] + "..." if len(comment[1]) > 50 else comment[1]
                            print(f"   - Film ID: {comment[0]}, Contenu: {content}, Date: {comment[2]}")
            except Exception as e:
                print(f"❌ Erreur lors de la vérification des commentaires: {str(e)}")
            
            # 3. Tester l'endpoint des statistiques
            print(f"\n🌐 TEST DE L'ENDPOINT /users/{user_id}/stats:")
            
            try:
                url = f"http://localhost:5000/api/users/{user_id}/stats"
                response = requests.get(url, timeout=10)
                
                print(f"📊 Status Code: {response.status_code}")
                print(f"📋 Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print("✅ Endpoint fonctionne!")
                    data = response.json()
                    print("📄 Données reçues:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Comparer avec les données de la DB
                    print(f"\n🔍 COMPARAISON DB vs ENDPOINT:")
                    print(f"   Likes - DB: {likes_count}, Endpoint: {data.get('likedMovies', 'N/A')}")
                    print(f"   Watchlist - DB: {watchlist_count}, Endpoint: {data.get('watchlistCount', 'N/A')}")
                    print(f"   Commentaires - DB: {comments_count}, Endpoint: {data.get('commentsCount', 'N/A')}")
                    
                elif response.status_code == 500:
                    print("❌ Erreur serveur 500")
                    print(f"Réponse: {response.text}")
                    
                    # Analyser l'erreur
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            print(f"💡 Erreur détaillée: {error_data['error']}")
                    except:
                        pass
                        
                else:
                    print(f"❌ Erreur {response.status_code}")
                    print(f"Réponse: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print("❌ Impossible de se connecter au serveur Flask")
                print("💡 Assurez-vous que le serveur est en cours d'exécution avec 'python app.py'")
            except Exception as e:
                print(f"❌ Erreur lors du test de l'endpoint: {str(e)}")
            
            # 4. Test des modèles Python
            print(f"\n🐍 TEST DES MODÈLES PYTHON:")
            
            try:
                from models.movie import Like, Comment
                print("✅ Modèles Like et Comment importés")
                
                # Test avec SQLAlchemy
                likes_count_sqlalchemy = db.session.query(Like).filter(Like.user_id == user_id).count()
                print(f"✅ Likes via SQLAlchemy: {likes_count_sqlalchemy}")
                
                comments_count_sqlalchemy = db.session.query(Comment).filter(Comment.user_id == user_id).count()
                print(f"✅ Commentaires via SQLAlchemy: {comments_count_sqlalchemy}")
                
            except ImportError as e:
                print(f"❌ Erreur d'import des modèles: {str(e)}")
            except Exception as e:
                print(f"❌ Erreur avec SQLAlchemy: {str(e)}")
            
            try:
                from models.watchlist import Watchlist
                print("✅ Modèle Watchlist importé")
                
                watchlist_count_sqlalchemy = db.session.query(Watchlist).filter(Watchlist.user_id == user_id).count()
                print(f"✅ Watchlist via SQLAlchemy: {watchlist_count_sqlalchemy}")
                
            except ImportError as e:
                print(f"❌ Erreur d'import du modèle Watchlist: {str(e)}")
            except Exception as e:
                print(f"❌ Erreur avec Watchlist SQLAlchemy: {str(e)}")
            
            # 5. Recommandations
            print(f"\n💡 RECOMMANDATIONS:")
            
            if likes_count == 0 and watchlist_count == 0 and comments_count == 0:
                print("🔧 PROBLÈME: Aucune donnée dans la base de données")
                print("   - Vérifiez que les actions (like, watchlist, comment) sont bien enregistrées")
                print("   - Testez manuellement l'ajout d'un like via l'interface")
            else:
                print("🔧 PROBLÈME: Les données existent mais l'endpoint ne les récupère pas")
                print("   - L'endpoint retourne une erreur 500")
                print("   - Vérifiez les imports des modèles dans user_controller.py")
                print("   - Vérifiez les relations entre les tables")
                print("   - Regardez les logs du serveur Flask pour plus de détails")
            
            print(f"\n✅ Diagnostic terminé pour l'utilisateur ID {user_id}")
            
    except Exception as e:
        print(f"❌ Erreur critique: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_profile_stats_issue()
