"""
Script pour créer des données de test si la base de données est vide
"""

import sys
import os
import datetime
import random

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app
    from database.db import db
    from models.user import User
    from sqlalchemy import text
    
    print("🔧 CRÉATION DE DONNÉES DE TEST")
    print("=" * 40)
    
    with app.app_context():
        # Vérifier si l'utilisateur ID 38 existe
        user = User.query.get(38)
        
        if not user:
            print("❌ Utilisateur ID 38 non trouvé")
            print("🔍 Recherche d'autres utilisateurs...")
            
            users = User.query.all()
            if users:
                print(f"✅ {len(users)} utilisateurs trouvés:")
                for u in users[:5]:
                    print(f"   - ID: {u.id}, Nom: {u.fullname}, Email: {u.email}")
                
                # Utiliser le premier utilisateur trouvé
                test_user = users[0]
                print(f"\n🎯 Utilisation de l'utilisateur ID {test_user.id} pour les tests")
            else:
                print("❌ Aucun utilisateur trouvé dans la base de données!")
                print("🔧 Création d'un utilisateur de test...")
                
                # Créer un utilisateur de test
                test_user = User(
                    fullname="Utilisateur Test",
                    email="test@example.com",
                    password="",
                    created_at=datetime.datetime.now()
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"✅ Utilisateur de test créé avec l'ID {test_user.id}")
        else:
            test_user = user
            print(f"✅ Utilisateur ID 38 trouvé: {user.fullname}")
        
        # Vérifier les tables nécessaires
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Créer des données de test pour les likes
        if 'likes' in tables:
            with db.engine.connect() as connection:
                # Vérifier s'il y a déjà des likes pour cet utilisateur
                result = connection.execute(text(f"SELECT COUNT(*) FROM likes WHERE user_id = {test_user.id}"))
                likes_count = result.scalar()
                
                if likes_count == 0:
                    print("🔧 Création de likes de test...")
                    # Créer quelques likes de test
                    for i in range(5):
                        movie_id = 1000 + i  # IDs de films fictifs
                        try:
                            connection.execute(text(
                                "INSERT INTO likes (user_id, movie_id, created_at) VALUES (:user_id, :movie_id, :created_at)"
                            ), {
                                'user_id': test_user.id,
                                'movie_id': movie_id,
                                'created_at': datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))
                            })
                            connection.commit()
                        except Exception as e:
                            print(f"⚠️ Erreur lors de la création du like {i}: {str(e)}")
                    print("✅ Likes de test créés")
                else:
                    print(f"✅ {likes_count} likes déjà présents pour l'utilisateur")
        
        # Créer des données de test pour la watchlist
        if 'watchlists' in tables:
            with db.engine.connect() as connection:
                result = connection.execute(text(f"SELECT COUNT(*) FROM watchlists WHERE user_id = {test_user.id}"))
                watchlist_count = result.scalar()
                
                if watchlist_count == 0:
                    print("🔧 Création d'éléments de watchlist de test...")
                    for i in range(3):
                        movie_id = 2000 + i
                        try:
                            connection.execute(text(
                                "INSERT INTO watchlists (user_id, movie_id, created_at) VALUES (:user_id, :movie_id, :created_at)"
                            ), {
                                'user_id': test_user.id,
                                'movie_id': movie_id,
                                'created_at': datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 15))
                            })
                            connection.commit()
                        except Exception as e:
                            print(f"⚠️ Erreur lors de la création de l'élément watchlist {i}: {str(e)}")
                    print("✅ Éléments de watchlist de test créés")
                else:
                    print(f"✅ {watchlist_count} éléments de watchlist déjà présents")
        
        # Créer des données de test pour les commentaires
        if 'comments' in tables:
            with db.engine.connect() as connection:
                result = connection.execute(text(f"SELECT COUNT(*) FROM comments WHERE user_id = {test_user.id}"))
                comments_count = result.scalar()
                
                if comments_count == 0:
                    print("🔧 Création de commentaires de test...")
                    for i in range(2):
                        movie_id = 3000 + i
                        try:
                            connection.execute(text(
                                "INSERT INTO comments (user_id, movie_id, content, created_at) VALUES (:user_id, :movie_id, :content, :created_at)"
                            ), {
                                'user_id': test_user.id,
                                'movie_id': movie_id,
                                'content': f"Commentaire de test {i+1} - Excellent film!",
                                'created_at': datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 10))
                            })
                            connection.commit()
                        except Exception as e:
                            print(f"⚠️ Erreur lors de la création du commentaire {i}: {str(e)}")
                    print("✅ Commentaires de test créés")
                else:
                    print(f"✅ {comments_count} commentaires déjà présents")
        
        print(f"\n🎯 UTILISEZ L'ID {test_user.id} POUR TESTER LA PAGE DE PROFIL")
        print(f"📧 Email: {test_user.email}")
        print(f"👤 Nom: {test_user.fullname}")
        
        print("\n✅ Création de données de test terminée")
        
except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()
