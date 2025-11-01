from flask import Flask
from .api import api_bp
from .web import web_bp

def create_app(ptb_app=None, webhook_secret: str | None = None, ptb_loop=None) -> Flask:
    app = Flask(
        __name__,
        static_folder="../statics",
        template_folder="../templates",
    )
    # Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Integración con PTB / Webhook
    if ptb_app:
        app.config["PTB_APP"] = ptb_app
    if webhook_secret:
        app.config["WEBHOOK_SECRET"] = webhook_secret
    if ptb_loop:
        app.config["PTB_LOOP"] = ptb_loop

    return app

