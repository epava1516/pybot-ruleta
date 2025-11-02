# app/utils/tg_webapp.py
import hmac, hashlib
from urllib.parse import parse_qsl

def verify_init_data(init_data: str, bot_token: str) -> bool:
    if not init_data or not bot_token:
        return False
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    their_hash = params.pop('hash', None)
    if not their_hash:
        return False
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calc_hash, their_hash)

