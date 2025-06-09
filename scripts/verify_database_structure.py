```typescriptreact file="app.py"
[v0-no-op-code-block-prefix]from flask import Flask, send_from_directory, request, jsonify, abort
from flask_cors import CORS
from flask_migrate import Migrate
from database import init_app
from database.db import db
from utils.rate_limiter import apply_global_rate_limiting
from utils.loop_detector import apply_loop_detection
import os
import logging
from werkzeug.exceptions import NotFound

# Initialize Flask app
app = init_app()
app.secret_key = 'ertdfgcvb'

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')

# Configuration Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['STATIC_FOLDER'] = STATIC_FOLDER

# Créer les dossiers s'ils n'existent pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Configuration CORS
CORS(app, 
     supports_credentials=True, 
     resources={
         r"/api/*": {
             "origins": ["http://localhost:5173", "http://127.0.0.1:5173"], 
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "expose_headers": ["Content-Type", "Authorization"]
         },
         r"/static/*": {
             "origins": ["http://localhost:5173", "http://127.0.0.1:5173"], 
             "methods": ["GET", "OPTIONS"]
         }
     })

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Route PRINCIPALE pour servir les fichiers uploadés
@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    """Sert les fichiers uploadés depuis le dossier uploads"""
    try:
        logger.info(f"🔍 Demande de fichier: {filename}")
        logger.info(f"📁 Dossier uploads: {UPLOAD_FOLDER}")
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        logger.info(f"📄 Chemin complet: {file_path}")
        logger.info(f"✅ Fichier existe: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ Fichier non trouvé: {file_path}")
            # Lister les fichiers disponibles pour debug
            if os.path.exists(UPLOAD_FOLDER):
                available_files = os.listdir(UPLOAD_FOLDER)
                logger.info(f"📋 Fichiers disponibles: {available_files}")
            abort(404)
            
        logger.info(f"✅ Envoi du fichier: {filename}")
        return send_from_directory(UPLOAD_FOLDER, filename)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi du fichier {filename}: {str(e)}")
        abort(500)

# Route de fallback pour tous les fichiers statiques
@app.route('/static/<path:path>')
def serve_static(path):
    """Sert tous les autres fichiers statiques"""
    try:
        logger.info(f"🔍 Demande de fichier statique: {path}")
        return send_from_directory(STATIC_FOLDER, path)
    except Exception as e:
        logger.error(f"❌ Erreur fichier statique {path}: {str(e)}")
        abort(404)

# Route de test pour vérifier les uploads
@app.route('/api/test-uploads')
def test_uploads():
    """Route de test pour vérifier la configuration des uploads"""
    try:
        files = []
        if os.path.exists(UPLOAD_FOLDER):
            files = os.listdir(UPLOAD_FOLDER)
            
        return jsonify({
            'status': 'success',
            'base_dir': BASE_DIR,
            'static_folder': STATIC_FOLDER,
            'upload_folder': UPLOAD_FOLDER,
            'upload_folder_exists': os.path.exists(UPLOAD_FOLDER),
            'static_folder_exists': os.path.exists(STATIC_FOLDER),
            'files': files,
            'file_count': len(files),
            'sample_urls': [f"http://localhost:5000/static/uploads/{f}" for f in files[:3]]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Route pour tester un fichier spécifique
@app.route('/api/test-file/<filename>')
def test_file(filename):
    """Test si un fichier spécifique existe"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    exists = os.path.exists(file_path)
    
    return jsonify({
        'filename': filename,
        'exists': exists,
        'full_path': file_path,
        'url': f"http://localhost:5000/static/uploads/{filename}" if exists else None
    })

# Middleware pour logger toutes les requêtes statiques
@app.before_request
def log_request_info():
    if request.path.startswith('/static/'):
        logger.info(f"🌐 Requête statique: {request.method} {request.path}")

# Configuration de la base de données
migrate = Migrate(app, db)

# Appliquer les protections
print("🛡️  Applying rate limiting and loop detection...")
apply_global_rate_limiting(app, max_requests_per_minute=100)  # Augmenter de 25 à 100
apply_loop_detection(app)

# Enregistrer les routes
from routes import register_routes
register_routes(app)

# Créer les tables
with app.app_context():
    db.create_all()

# Route OPTIONS pour CORS
@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 200

# Route racine
@app.route('/')
def index():
    return "L'API fonctionne bien 🧠 !"

# Gestionnaire d'erreur 404 personnalisé
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/static/uploads/'):
        logger.error(f"❌ 404 - Fichier non trouvé: {request.path}")
        return jsonify({'error': 'Fichier non trouvé'}), 404
    return jsonify({'error': 'Page non trouvée'}), 404

if __name__ == '__main__':
    print("🚀 Démarrage du serveur Flask...")
    print(f"📁 Dossier base: {BASE_DIR}")
    print(f"📁 Dossier static: {STATIC_FOLDER}")
    print(f"📁 Dossier uploads: {UPLOAD_FOLDER}")
    print(f"📁 Uploads existe: {os.path.exists(UPLOAD_FOLDER)}")
    print(f"📁 Static existe: {os.path.exists(STATIC_FOLDER)}")
    
    if os.path.exists(UPLOAD_FOLDER):
        files = os.listdir(UPLOAD_FOLDER)
        print(f"📋 Fichiers dans uploads: {len(files)}")
        for f in files[:3]:  # Afficher les 3 premiers fichiers
            print(f"   - {f}")
    
    print("🛡️  Rate limits appliqués:")
    print("   - Endpoints API généraux: 25 requêtes/minute")
    print("   - Endpoints données utilisateur: 15 requêtes/minute") 
    print("   - Recommandations: 5 requêtes/minute")
    print("🔍 Détection de boucles infinies: Active")
    print("🌐 Serveur démarré sur http://localhost:5000")
    print("🧪 Test des uploads: http://localhost:5000/api/test-uploads")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
