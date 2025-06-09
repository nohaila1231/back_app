"""
Script pour ajouter le champ created_at à la table users en utilisant SQL direct
"""

import sys
import os
import datetime
import random
import psycopg2
from psycopg2 import sql

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Importer la configuration de la base de données
    from app import app
    
    print("✅ Application Flask importée avec succès")
    
    # Récupérer l'URL de connexion à la base de données
    with app.app_context():
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_url:
            raise ValueError("SQLALCHEMY_DATABASE_URI n'est pas défini dans la configuration")
    
    print(f"✅ URL de la base de données récupérée")
    
    # Connexion directe à PostgreSQL
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Connexion à la base de données établie")
    
    # Vérifier si la colonne existe déjà
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='created_at'")
    column_exists = cursor.fetchone() is not None
    
    if not column_exists:
        print("🔄 Ajout de la colonne created_at à la table users...")
        
        # Ajouter la colonne avec une valeur par défaut
        cursor.execute(
            sql.SQL("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        )
        print("✅ Colonne created_at ajoutée")
    else:
        print("✅ La colonne created_at existe déjà dans la table users")
    
    # Récupérer les utilisateurs sans date de création
    cursor.execute("SELECT id FROM users WHERE created_at IS NULL")
    users_without_date = cursor.fetchall()
    
    if users_without_date:
        print(f"🔄 {len(users_without_date)} utilisateurs n'ont pas de date de création, mise à jour...")
        
        now = datetime.datetime.now()
        
        # Mettre à jour chaque utilisateur avec une date aléatoire
        for user_id in users_without_date:
            # Date aléatoire entre maintenant et il y a 12 mois
            days_ago = random.randint(0, 365)
            random_date = now - datetime.timedelta(days=days_ago)
            
            cursor.execute(
                sql.SQL("UPDATE users SET created_at = %s WHERE id = %s"),
                (random_date, user_id[0])
            )
        
        print(f"✅ Dates de création générées pour {len(users_without_date)} utilisateurs")
    else:
        print("✅ Tous les utilisateurs ont déjà une date de création")
    
    # Afficher quelques statistiques
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Définir 'now' pour les statistiques
    now = datetime.datetime.now()
    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= %s", (now - datetime.timedelta(days=30),))
    recent_users = cursor.fetchone()[0]

    print(f"📊 Statistiques:")
    print(f"   - Total utilisateurs: {total_users}")
    print(f"   - Utilisateurs récents (30 derniers jours): {recent_users}")
    
    # Fermer la connexion
    cursor.close()
    conn.close()
    
    print("✅ Migration terminée avec succès")
    
except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()
