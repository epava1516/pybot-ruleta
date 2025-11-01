from flask import Flask
from .api import api_bp
from .web import web_bp

def create_app(ptb_app=None, webhook_path: str | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder="../statics",
        template_folder="../templates",
    )
    # Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Integración con PTB y webhook
    if ptb_app:
        app.config["PTB_APP"] = ptb_app
    if webhook_path:
        app.config["WEBHOOK_PATH"] = webhook_path

    return app

