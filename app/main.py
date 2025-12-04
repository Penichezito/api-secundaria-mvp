from flask import Flask
from flask_cors import CORS
from app.config import config
from app.routes.files import files_bp

def create_app():
    """Factory para criar a aplicação Flask"""
    app = Flask(__name__)

    # Configurações da aplicação
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE

    # Inicializa diretórios 
    config.init_app()

    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://frontend:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type"]
        } 
    })

    # Registro dos Blueprints
    app.register_blueprint(files_bp)

    # Rota raiz
    @app.route("/")
    def index():
        return {
            'message': 'API Secundária - Freela Facility',
            'version': '1.0.0',
            'status': 'online',
            'endpoints': {
                'process_file': 'POST /api/files/process',
                'get_file_tags': 'GET /api/files/<id>/tags',
                'update_tags': 'PUT /api/files/<id>/tags',
                'search_files': 'POST /api/files/search',
                'list_files': 'GET /api/files',
                'get_file': 'GET /api/files/<id>',
                'delete_file': 'DELETE /api/files/<id>',
                'statistics': 'GET /api/files/statistics',
                'health': 'GET /api/files/health'
            }
        }
    
    # Erros handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Endpoint não encontrado."}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Erro interno do servidor."}, 500
    
    @app.errorhandler(413)
    def request_entity_too_larger(error):
        max_mb = config.MAX_FILE_SIZE / (1024 * 1024)
        return {"error": f"Arquivo muito grande. Tamanho máximo permitido é {max_mb} MB."}, 413
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)

