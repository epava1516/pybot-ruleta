from pydantic import BaseModel, field_validator

class RollIn(BaseModel):
    chat_id: int | str
    n: int
    @field_validator("n")
    @classmethod
    def validate_n(cls, v):
        if not (0 <= v <= 36):
            raise ValueError("n debe estar entre 0 y 36")
        return v

class ChatIn(BaseModel):
    chat_id: int | str

class WindowIn(BaseModel):
    chat_id: int | str
    size: int
    @field_validator("size")
    @classmethod
    def validate_size(cls, v):
        if v <= 0 or v > 5000:
            raise ValueError("size inválido")
        return v

class ConfigIn(BaseModel):
    chat_id: int | str
    window: int
    history_cap: int | None = None
    use_zero: bool | None = None
    seed_last: int | None = None   # cuantos del historial copiar al reset
    hist_tail: int | None = None

    @field_validator("window")
    @classmethod
    def v_window(cls, v):
        if v <= 0 or v > 5000:
            raise ValueError("window inválido")
        return v

    @field_validator("history_cap")
    @classmethod
    def v_cap(cls, v):
        if v is None: return v
        if v <= 0 or v > 1000:
            raise ValueError("history_cap inválido")
        return v

    @field_validator("seed_last")
    @classmethod
    def v_seed(cls, v):
        if v is None: return v
        if v < 0 or v > 5000:
            raise ValueError("seed_last inválido")
        return v
