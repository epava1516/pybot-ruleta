from flask import Flask
from config import TOKEN, REDIRECT_URL, RESTRICT_TO_TELEGRAM, GATE_STRICT
from .api import api_bp
from .web import web_bp

def create_app(ptb_app=None, webhook_secret: str | None = None, ptb_loop=None) -> Flask:
    app = Flask(
        __name__,
        static_folder="../statics",
        template_folder="../templates",
    )
    app.config.update(
        TOKEN=TOKEN,
        REDIRECT_URL=REDIRECT_URL,
        RESTRICT_TO_TELEGRAM=RESTRICT_TO_TELEGRAM,
        GATE_STRICT=GATE_STRICT,
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

