import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from models.movie import Movie
from models.like import Like
from models.watchlist import Watchlist
from models.comment import Comment
from database.db import db
from sqlalchemy import func, desc, text
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.content_based_model = None
        self.collaborative_model = None
        self.movie_features = None
        self.movie_ids = None
    
    def train_content_based_model(self):
        """Entraîne le modèle de recommandation basé sur le contenu"""
        try:
            # Récupérer tous les films de la base de données
            movies = Movie.query.all()
            
            if not movies:
                logger.warning("Aucun film trouvé pour l'entraînement du modèle")
                return False
            
            # Créer un DataFrame avec les caractéristiques des films
            movie_data = []
            for movie in movies:
                # Combiner le titre, la description et les genres pour créer un "document" par film
                content = f"{movie.title} {movie.overview} {movie.genres}"
                movie_data.append({
                    'id': movie.id,
                    'content': content,
                    'popularity': movie.popularity or 0
                })
            
            df = pd.DataFrame(movie_data)
            
            # Utiliser TF-IDF pour vectoriser le contenu textuel
            tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
            tfidf_matrix = tfidf.fit_transform(df['content'].fillna(''))
            
            # Calculer la similarité cosinus entre les films
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # Stocker les résultats pour une utilisation ultérieure
            self.content_based_model = cosine_sim
            self.movie_ids = df['id'].tolist()
            
            logger.info(f"Modèle basé sur le contenu entraîné avec succès sur {len(movies)} films")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle basé sur le contenu: {str(e)}")
            return False
    
    def train_collaborative_model(self):
        """Entraîne le modèle de filtrage collaboratif"""
        try:
            # Récupérer toutes les interactions utilisateur-film
            likes = Like.query.all()
            watchlist_items = Watchlist.query.all()
            comments = Comment.query.all()
            
            if not (likes or watchlist_items or comments):
                logger.warning("Aucune interaction utilisateur-film trouvée pour l'entraînement du modèle collaboratif")
                return False
            
            # Créer un DataFrame pour les interactions
            interactions = []
            
            # Ajouter les likes (poids élevé)
            for like in likes:
                interactions.append({
                    'user_id': like.user_id,
                    'movie_id': like.movie_id,
                    'weight': 5.0  # Poids élevé pour les likes
                })
            
            # Ajouter les éléments de la watchlist (poids moyen)
            for item in watchlist_items:
                interactions.append({
                    'user_id': item.user_id,
                    'movie_id': item.movie_id,
                    'weight': 3.0  # Poids moyen pour la watchlist
                })
            
            # Ajouter les commentaires (poids moyen-faible)
            for comment in comments:
                interactions.append({
                    'user_id': comment.user_id,
                    'movie_id': comment.movie_id,
                    'weight': 2.0  # Poids moyen-faible pour les commentaires
                })
            
            if not interactions:
                logger.warning("Aucune interaction à traiter")
                return False
            
            # Créer un DataFrame
            df_interactions = pd.DataFrame(interactions)
            
            # Créer une matrice utilisateur-film
            user_movie_matrix = df_interactions.pivot_table(
                index='user_id', 
                columns='movie_id', 
                values='weight', 
                aggfunc='mean',
                fill_value=0
            )
            
            # Calculer la similarité entre les utilisateurs
            user_similarity = cosine_similarity(user_movie_matrix)
            
            # Stocker les résultats
            self.collaborative_model = {
                'user_similarity': user_similarity,
                'user_movie_matrix': user_movie_matrix
            }
            
            logger.info(f"Modèle collaboratif entraîné avec succès sur {len(df_interactions)} interactions")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle collaboratif: {str(e)}")
            return False
    
    def get_content_based_recommendations(self, movie_ids, top_n=10):
        """
        Obtient des recommandations basées sur le contenu pour une liste de films
        """
        if self.content_based_model is None:
            success = self.train_content_based_model()
            if not success:
                return []
        
        # Initialiser un score pour chaque film
        sim_scores = np.zeros(len(self.movie_ids))
        
        # Pour chaque film d'entrée, ajouter sa similarité avec tous les autres films
        for movie_id in movie_ids:
            try:
                idx = self.movie_ids.index(movie_id)
                sim_scores += self.content_based_model[idx]
            except (ValueError, IndexError):
                # Ignorer les films qui ne sont pas dans notre modèle
                continue
        
        # Créer une liste de tuples (id du film, score de similarité)
        movie_scores = list(zip(self.movie_ids, sim_scores))
        
        # Trier par score de similarité
        movie_scores = sorted(movie_scores, key=lambda x: x[1], reverse=True)
        
        # Filtrer les films d'entrée
        movie_scores = [(movie_id, score) for movie_id, score in movie_scores if movie_id not in movie_ids]
        
        # Retourner les top_n films
        top_movies = [movie_id for movie_id, _ in movie_scores[:top_n]]
        
        return top_movies
    
    def get_collaborative_recommendations(self, user_id, top_n=10):
        """
        Obtient des recommandations basées sur le filtrage collaboratif pour un utilisateur
        """
        if self.collaborative_model is None:
            success = self.train_collaborative_model()
            if not success:
                return []
        
        user_similarity = self.collaborative_model['user_similarity']
        user_movie_matrix = self.collaborative_model['user_movie_matrix']
        
        # Vérifier si l'utilisateur est dans notre modèle
        if user_id not in user_movie_matrix.index:
            return []
        
        # Trouver l'index de l'utilisateur
        user_idx = list(user_movie_matrix.index).index(user_id)
        
        # Calculer les scores de recommandation
        user_sim = user_similarity[user_idx]
        
        # Pondérer les films par similarité utilisateur
        weighted_scores = user_sim.reshape(-1, 1) * user_movie_matrix.values
        
        # Calculer le score moyen pour chaque film
        scores = np.sum(weighted_scores, axis=0) / (np.sum(user_sim) + 1e-10)
        
        # Créer un DataFrame avec les scores
        movie_scores = pd.DataFrame({
            'movie_id': user_movie_matrix.columns,
            'score': scores
        })
        
        # Filtrer les films que l'utilisateur a déjà vus
        user_movies = user_movie_matrix.loc[user_id]
        user_movies = user_movies[user_movies > 0].index.tolist()
        movie_scores = movie_scores[~movie_scores['movie_id'].isin(user_movies)]
        
        # Trier par score
        movie_scores = movie_scores.sort_values('score', ascending=False)
        
        # Retourner les top_n films
        top_movies = movie_scores['movie_id'].tolist()[:top_n]
        
        return top_movies
    
    def get_popularity_recommendations(self, top_n=10):
        """
        Obtient des recommandations basées sur la popularité des films
        """
        try:
            # Récupérer les films les plus populaires
            popular_movies = Movie.query.order_by(desc(Movie.popularity)).limit(top_n).all()
            return [movie.id for movie in popular_movies]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des films populaires: {str(e)}")
            return []
    
    def get_hybrid_recommendations(self, user_id, top_n=20):
        """
        Combine les recommandations basées sur le contenu et le filtrage collaboratif
        """
        try:
            # Récupérer les films aimés et dans la watchlist de l'utilisateur
            liked_movies = db.session.query(Like.movie_id).filter(Like.user_id == user_id).all()
            liked_movie_ids = [movie_id for (movie_id,) in liked_movies]
            
            watchlist_movies = db.session.query(Watchlist.movie_id).filter(Watchlist.user_id == user_id).all()
            watchlist_movie_ids = [movie_id for (movie_id,) in watchlist_movies]
            
            # Récupérer les films commentés par l'utilisateur
            commented_movies = db.session.query(Comment.movie_id).filter(Comment.user_id == user_id).all()
            commented_movie_ids = [movie_id for (movie_id,) in commented_movies]
            
            # Combiner les listes
            user_movies = list(set(liked_movie_ids + watchlist_movie_ids + commented_movie_ids))
            
            # Si l'utilisateur n'a pas d'historique, retourner des recommandations basées sur la popularité
            if not user_movies:
                logger.info(f"Aucun historique pour l'utilisateur {user_id}, utilisation des recommandations par popularité")
                return self.get_popularity_recommendations(top_n)
            
            # Obtenir des recommandations basées sur le contenu
            content_recs = self.get_content_based_recommendations(user_movies, top_n=top_n)
            
            # Obtenir des recommandations collaboratives
            collab_recs = self.get_collaborative_recommendations(user_id, top_n=top_n)
            
            # Combiner les recommandations avec une pondération
            # Donner plus de poids aux recommandations collaboratives si disponibles
            all_recs = []
            
            if collab_recs:
                all_recs.extend([(movie_id, 0.7) for movie_id in collab_recs])
            
            if content_recs:
                all_recs.extend([(movie_id, 0.3) for movie_id in content_recs])
            
            # Si aucune recommandation n'est disponible, utiliser la popularité
            if not all_recs:
                return self.get_popularity_recommendations(top_n)
            
            # Agréger les scores pour les films qui apparaissent dans les deux listes
            movie_scores = {}
            for movie_id, weight in all_recs:
                if movie_id in movie_scores:
                    movie_scores[movie_id] += weight
                else:
                    movie_scores[movie_id] = weight
            
            # Trier par score
            sorted_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Retourner les top_n films uniques
            unique_movies = []
            for movie_id, _ in sorted_movies:
                if movie_id not in unique_movies and movie_id not in user_movies:
                    unique_movies.append(movie_id)
                if len(unique_movies) >= top_n:
                    break
            
            # Si nous n'avons pas assez de recommandations, compléter avec des films populaires
            if len(unique_movies) < top_n:
                popular_recs = self.get_popularity_recommendations(top_n)
                for movie_id in popular_recs:
                    if movie_id not in unique_movies and movie_id not in user_movies:
                        unique_movies.append(movie_id)
                    if len(unique_movies) >= top_n:
                        break
            
            return unique_movies[:top_n]
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des recommandations hybrides: {str(e)}")
            return self.get_popularity_recommendations(top_n)

# Créer une instance du service
recommendation_service = RecommendationService()

def get_recommendations_for_user(user_id, limit=10):
    """
    Fonction principale pour obtenir des recommandations pour un utilisateur
    """
    try:
        # Obtenir les IDs des films recommandés
        movie_ids = recommendation_service.get_hybrid_recommendations(user_id, top_n=limit)
        
        # Récupérer les détails complets des films
        # Utiliser une requête SQL brute pour éviter les problèmes de transaction
        movies = []
        if movie_ids:
            # Utiliser une nouvelle session pour éviter les problèmes de transaction
            with db.engine.connect() as conn:
                for movie_id in movie_ids:
                    result = conn.execute(text(f"SELECT * FROM movies WHERE id = {movie_id}"))
                    movie_data = result.fetchone()
                    if movie_data:
                        # Créer un objet Movie à partir des données
                        movie = Movie(
                            id=movie_data[0],
                            title=movie_data[1],
                            overview=movie_data[2],
                            poster_path=movie_data[3],
                            genres=movie_data[4],
                            popularity=movie_data[5],
                            release_date=movie_data[6]
                        )
                        movies.append(movie)
        
        if not movies:
            # En cas d'erreur ou si aucun film n'est trouvé, retourner les films populaires
            with db.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM movies ORDER BY popularity DESC LIMIT {limit}"))
                for row in result:
                    movie = Movie(
                        id=row[0],
                        title=row[1],
                        overview=row[2],
                        poster_path=row[3],
                        genres=row[4],
                        popularity=row[5],
                        release_date=row[6]
                    )
                    movies.append(movie)
        
        return movies
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des recommandations: {str(e)}")
        # En cas d'erreur, retourner une liste vide
        return []

def train_recommendation_models():
    """
    Fonction pour entraîner les modèles de recommandation
    """
    content_success = recommendation_service.train_content_based_model()
    collab_success = recommendation_service.train_collaborative_model()
    return content_success and collab_success
