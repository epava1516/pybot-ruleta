import json
from pathlib import Path
from config import DATA_FILE  # usar el path desde variables de entorno

# asegurar carpeta de datos
data_parent = Path(DATA_FILE).parent
data_parent.mkdir(parents=True, exist_ok=True)

# ================= Defaults =================
DEFAULT_CFG = {
    "window": 15,         # capacidad máx. de la ventana
    "history_cap": 20,    # cuántas tiradas mostrar (solo UI)
    "use_zero": True,     # siembra: incluir 0 (solo UI / futuro)
    "seed_last": 0,       # reservado (siembra de ventana)
    "hist_tail": 0,       # 0 = usar ventana; >0 = usar siempre K últimas del historial
}

# ================= I/O =================
def _load_raw():
    if not Path(DATA_FILE).exists():
        return {"chats": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def _save_raw(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _ensure_chat_struct(ch):
    """Soporta formato antiguo (lista simple) -> migra a {history, window, cfg}."""
    if isinstance(ch, list):
        history = ch[:]
        window  = history[-DEFAULT_CFG["window"]:]
        return {"history": history, "window": window, "cfg": DEFAULT_CFG.copy()}
    ch.setdefault("history", [])
    ch.setdefault("window", [])
    ch.setdefault("cfg", DEFAULT_CFG.copy())
    for k, v in DEFAULT_CFG.items():
        ch["cfg"].setdefault(k, v)
    return ch

def _get_all():
    data = _load_raw()
    data.setdefault("chats", {})
    changed = False
    for cid, ch in list(data["chats"].items()):
        new_ch = _ensure_chat_struct(ch)
        if new_ch is not ch:
            data["chats"][cid] = new_ch
            changed = True
    if changed:
        _save_raw(data)
    return data

def _get_chat_node(data, chat_id: str):
    chat_id = str(chat_id)
    if chat_id not in data["chats"]:
        data["chats"][chat_id] = _ensure_chat_struct({})
    return data["chats"][chat_id]

# ================= Public API =================
def get_cfg(chat_id):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    return ch["cfg"].copy()

def set_cfg(chat_id, **updates):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    ch["cfg"].update({k: v for k, v in updates.items() if k in DEFAULT_CFG})
    _save_raw(data)
    return ch["cfg"].copy()

def add_roll(chat_id, number: int):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    ch["history"].append(number)

    cap = int(ch["cfg"].get("window", DEFAULT_CFG["window"])) or DEFAULT_CFG["window"]
    ch["window"].append(number)
    if len(ch["window"]) > cap:
        ch["window"] = ch["window"][-cap:]

    _save_raw(data)

def rollback_roll(chat_id):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    if ch["history"]:
        last = ch["history"].pop()
        if ch["window"] and ch["window"][-1] == last:
            ch["window"].pop()
        _save_raw(data)

def reset_window(chat_id):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    ch["window"] = []
    _save_raw(data)

def get_history(chat_id):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    return ch["history"][:]

def get_window(chat_id):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    return ch["window"][:]

# ================= Stats =================
ROJO = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
NEGRO = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
FILA_SUPERIOR = {1,4,7,10,13,16,19,22,25,28,31,34}
FILA_CENTRAL  = {2,5,8,11,14,17,20,23,26,29,32,35}
FILA_INFERIOR = {3,6,9,12,15,18,21,24,27,30,33,36}

def _numbers_with_color(seq):
    out = []
    for n in seq:
        if n == 0:
            c = "🟢"
        elif n in ROJO:
            c = "🔴"
        else:
            c = "⚫"
        out.append((n, c))
    return out

def compute_stats(chat_id):
    data = _get_all()
    ch = _get_chat_node(data, chat_id)
    cfg = ch["cfg"]
    cap = int(cfg.get("window", DEFAULT_CFG["window"])) or DEFAULT_CFG["window"]
    k   = int(cfg.get("hist_tail", 0)) or 0

    if k > 0:
        use = ch["history"][-min(k, cap):]
        source = "history"
    else:
        use = ch["window"][-cap:]
        source = "window"

    total = len(use)
    if total == 0:
        return {
            "numbers": [],
            "counts": {}, "percents": {},
            "since_last_0": 0,
            "_meta": {"source": source, "window_capacity": cap, "hist_tail": k}
        }

    counts = {}
    counts["rojo"]  = sum(1 for n in use if n in ROJO)
    counts["negro"] = sum(1 for n in use if n in NEGRO)
    counts["par"]   = sum(1 for n in use if n != 0 and n % 2 == 0)
    counts["impar"] = sum(1 for n in use if n % 2 == 1)
    counts["bajos"] = sum(1 for n in use if 1 <= n <= 18)
    counts["altos"] = sum(1 for n in use if 19 <= n <= 36)
    counts["cero"]  = use.count(0)

    counts["docenas"] = [
        sum(1 for n in use if 1  <= n <= 12),
        sum(1 for n in use if 13 <= n <= 24),
        sum(1 for n in use if 25 <= n <= 36),
    ]
    counts["filas"] = [
        sum(1 for n in use if n in FILA_SUPERIOR),
        sum(1 for n in use if n in FILA_CENTRAL),
        sum(1 for n in use if n in FILA_INFERIOR),  # <-- corregido
    ]

    def pct(v): return round(100 * v / total, 1) if total else 0.0
    perc = {k: pct(v) for k, v in counts.items() if k not in ("docenas", "filas")}
    perc["docenas"] = [pct(x) for x in counts["docenas"]]
    perc["filas"]   = [pct(x) for x in counts["filas"]]

    since0 = 0
    for n in reversed(use):
        if n == 0:
            break
        since0 += 1

    return {
        "numbers": _numbers_with_color(use),
        "counts": counts,
        "percents": perc,
        "since_last_0": since0,
        "_meta": {"source": source, "window_capacity": cap, "hist_tail": k}
    }

