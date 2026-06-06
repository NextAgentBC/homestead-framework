from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from .cli import blog_cli, site_cli, token_cli
from .config import Config
from .extensions import db, migrate
from .routes.admin import bp as admin_bp
from .routes.public import bp as public_bp


def create_app(config_object=Config):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    app.register_blueprint(public_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.cli.add_command(blog_cli)
    app.cli.add_command(token_cli)
    app.cli.add_command(site_cli)

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": {"code": "not_found", "message": "Resource not found"}}), 404

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": {"code": "server_error", "message": "Unexpected server error"}}), 500

    return app


app = create_app()
