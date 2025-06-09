from repositories.comment_repository import (
    add_comment, get_comments_by_movie, get_comment_by_id,
    update_comment, delete_comment, like_comment, unlike_comment,
    is_comment_liked_by_user
)

def add_user_comment(user_id, movie_id, content, parent_id=None):
    """Ajoute un commentaire ou une réponse."""
    try:
        print(f"Service: Adding comment for user {user_id}, movie {movie_id}")
        
        if not content or not content.strip():
            print("Service: Empty content provided")
            return None
            
        comment = add_comment(user_id, movie_id, content.strip(), parent_id)
        print(f"Service: Comment added with ID {comment.id if comment else 'None'}")
        return comment
        
    except Exception as e:
        print(f"Service error in add_user_comment: {e}")
        return None

def get_movie_comments(movie_id):
    """Récupère tous les commentaires d'un film."""
    try:
        print(f"Service: Getting comments for movie {movie_id}")
        comments = get_comments_by_movie(movie_id)
        print(f"Service: Found {len(comments)} comments")
        return comments
        
    except Exception as e:
        print(f"Service error in get_movie_comments: {e}")
        return []

def update_user_comment(comment_id, user_id, content):
    """Met à jour un commentaire si l'utilisateur en est le propriétaire."""
    try:
        print(f"Service: Updating comment {comment_id} by user {user_id}")
        
        if not content or not content.strip():
            print("Service: Empty content provided for update")
            return None
        
        comment = get_comment_by_id(comment_id)
        if not comment:
            print(f"Service: Comment {comment_id} not found")
            return None
        
        if comment.user_id != user_id:
            print(f"Service: User {user_id} not authorized to update comment {comment_id}")
            return None
        
        updated_comment = update_comment(comment_id, content.strip())
        print(f"Service: Comment updated successfully")
        return updated_comment
        
    except Exception as e:
        print(f"Service error in update_user_comment: {e}")
        return None

def delete_user_comment(comment_id, user_id):
    """Supprime un commentaire si l'utilisateur en est le propriétaire."""
    try:
        print(f"Service: Deleting comment {comment_id} by user {user_id}")
        
        comment = get_comment_by_id(comment_id)
        if not comment:
            print(f"Service: Comment {comment_id} not found")
            return False
        
        if comment.user_id != user_id:
            print(f"Service: User {user_id} not authorized to delete comment {comment_id}")
            return False
        
        result = delete_comment(comment_id)
        print(f"Service: Comment deleted successfully: {result}")
        return result
        
    except Exception as e:
        print(f"Service error in delete_user_comment: {e}")
        return False

def toggle_comment_like(user_id, comment_id):
    """Toggle le like d'un commentaire."""
    try:
        print(f"Service: Toggling like for comment {comment_id} by user {user_id}")
        
        # Vérifier que le commentaire existe
        comment = get_comment_by_id(comment_id)
        if not comment:
            print(f"Service: Comment {comment_id} not found")
            return False
        
        if is_comment_liked_by_user(user_id, comment_id):
            print(f"Service: Removing like")
            result = unlike_comment(user_id, comment_id)
            return not result  # False si unlike réussi (plus liké)
        else:
            print(f"Service: Adding like")
            result = like_comment(user_id, comment_id)
            return result is not None  # True si like réussi
            
    except Exception as e:
        print(f"Service error in toggle_comment_like: {e}")
        return False
