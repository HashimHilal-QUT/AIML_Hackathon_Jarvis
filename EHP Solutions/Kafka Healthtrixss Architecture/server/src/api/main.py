from flask import Flask
from flask_cors import CORS
from src.common.config import Config
from src.api.routes import api_bp
from os import getenv

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    return app

if __name__ == '__main__':
    app = create_app()
    host = getenv('API_HOST', '0.0.0.0')
    port = int(getenv('API_PORT', 5000))
    debug = getenv('DEBUG', 'False').lower() == 'true'
    
    print("Starting API server...")
    print(f"Listening on {host}:{port}")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule}")
    
    app.run(host=host, port=port, debug=debug)