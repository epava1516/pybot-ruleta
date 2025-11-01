import re
import asyncio
import contextlib

# Cloudflare por defecto (no requiere cuenta para túnel efímero).
# ngrok si pasas token (desde config).

async def _cloudflared_url_from_stdout(proc) -> str | None:
    pat = re.compile(rb"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        m = pat.search(line)
        if m:
            return m.group(0).decode()
    return None

@contextlib.asynccontextmanager
async def cloudflare_tunnel(port: int):
    proc = await asyncio.create_subprocess_exec(
        "cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    url = await _cloudflared_url_from_stdout(proc)
    if not url:
        proc.terminate()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(proc.wait(), timeout=5)
        raise RuntimeError("No se pudo obtener la URL de cloudflared")
    try:
        yield url
    finally:
        if proc and proc.returncode is None:
            proc.terminate()
            with contextlib.suppress(Exception):
                await asyncio.wait_for(proc.wait(), timeout=5)

@contextlib.asynccontextmanager
async def ngrok_tunnel(port: int, authtoken: str):
    from pyngrok import ngrok
    ngrok.set_auth_token(authtoken)
    tunnel = ngrok.connect(addr=port, proto="http")
    try:
        yield tunnel.public_url
    finally:
        ngrok.disconnect(tunnel.public_url)
        ngrok.kill()

@contextlib.asynccontextmanager
async def maybe_tunnel(port: int, prefer: str = "cloudflare", ngrok_token: str | None = None):
    if prefer == "ngrok" and ngrok_token:
        async with ngrok_tunnel(port, ngrok_token) as url:
            yield url
            return
    async with cloudflare_tunnel(port) as url:
        yield url
