from flask import Blueprint

api_bp = Blueprint("api", __name__)

# Importa las rutas para registrar los endpoints en el blueprint
from . import routes  # noqa: F401
