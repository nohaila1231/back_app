# Créez ce fichier pour tester les imports
try:
    print("Testing imports...")
    
    from models.comment import Comment
    print("✓ Comment model imported successfully")
    
    from models.comment_like import CommentLike
    print("✓ CommentLike model imported successfully")
    
    from models.user import User
    print("✓ User model imported successfully")
    
    from models.movie import Movie
    print("✓ Movie model imported successfully")
    
    # Test de création d'objets
    print("\nTesting model creation...")
    
    # Ne pas sauvegarder, juste tester la création
    test_comment = Comment(user_id=1, movie_id=1, content="test")
    print("✓ Comment object created successfully")
    
    test_like = CommentLike(user_id=1, comment_id=1)
    print("✓ CommentLike object created successfully")
    
    print("\nAll imports and model creation tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")