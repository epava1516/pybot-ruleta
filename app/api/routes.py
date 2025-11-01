from flask import request, jsonify, make_response
from . import api_bp
from storage import (
    add_roll, rollback_roll, reset_window, compute_stats,
    get_cfg, set_cfg
)
import hashlib

def _make_etag(data: dict) -> str:
    """ETag estable solo con lo que pinta la UI."""
    meta = data.get("_meta", {}) or {}
    nums = data.get("numbers", []) or []
    # Lista de enteros solamente (ignora emoji)
    nums_str = ",".join(str(n) for n, _c in nums)
    src = f"{meta.get('source','')}|{meta.get('window_capacity','')}|{meta.get('hist_tail','')}|{nums_str}"
    h = hashlib.blake2s(src.encode("utf-8"), digest_size=8).hexdigest()
    return f"\"{h}\""  # comillas por especificación

def _match_inm(inm_header: str | None, server_etag: str) -> bool:
    """
    If-None-Match puede traer varios ETags separados por comas y/o prefijo W/.
    Normalizamos quitando W/ y comillas.
    """
    if not inm_header:
        return False

    def norm(s: str) -> str:
        s = s.strip()
        if s.startswith("W/"):
            s = s[2:].strip()
        if s.startswith('"') and s.endswith('"') and len(s) >= 2:
            s = s[1:-1]
        return s

    server_norm = norm(server_etag)
    for token in inm_header.split(","):
        if norm(token) == server_norm:
            return True
    return False

@api_bp.get("/stats")
def stats():
    chat_id = request.args.get("chat_id")
    if not chat_id:
        return jsonify({"error": "chat_id requerido"}), 400
    try:
        data = compute_stats(chat_id)
        etag = _make_etag(data)

        inm = request.headers.get("If-None-Match")
        if _match_inm(inm, etag):
            resp = make_response("", 304)
            resp.headers["ETag"] = etag
            resp.headers["Cache-Control"] = "no-cache"
            return resp

        resp = jsonify({"stats": data, "window": data["_meta"].get("window_capacity")})
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "no-cache"
        return resp, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.post("/roll")
def roll():
    body = request.get_json(silent=True) or {}
    chat_id = body.get("chat_id")
    n = body.get("n")
    if chat_id is None or n is None:
        return jsonify({"error": "chat_id y n requeridos"}), 400
    try:
        n = int(n)
        if not (0 <= n <= 36):
            return jsonify({"error": "n fuera de rango (0–36)"}), 400
        add_roll(chat_id, n)
        data = compute_stats(chat_id)
        return jsonify({"ok": True, "stats": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.post("/rollback")
def rollback():
    body = request.get_json(silent=True) or {}
    chat_id = body.get("chat_id")
    if chat_id is None:
        return jsonify({"error": "chat_id requerido"}), 400
    try:
        rollback_roll(chat_id)
        data = compute_stats(chat_id)
        return jsonify({"ok": True, "stats": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.post("/reset")
def reset():
    body = request.get_json(silent=True) or {}
    chat_id = body.get("chat_id")
    if chat_id is None:
        return jsonify({"error": "chat_id requerido"}), 400
    try:
        reset_window(chat_id)
        data = compute_stats(chat_id)
        return jsonify({"ok": True, "stats": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.get("/config")
def get_config():
    chat_id = request.args.get("chat_id")
    if not chat_id:
        return jsonify({"error": "chat_id requerido"}), 400
    try:
        return jsonify(get_cfg(chat_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.post("/config")
def set_config():
    body = request.get_json(silent=True) or {}
    chat_id = body.get("chat_id")
    if not chat_id:
        return jsonify({"error": "chat_id requerido"}), 400
    try:
        payload = {k: body[k] for k in ("window","history_cap","hist_tail") if k in body}
        out = set_cfg(chat_id, **payload)
        data = compute_stats(chat_id)
        return jsonify({"ok": True, "config": out, "stats": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
