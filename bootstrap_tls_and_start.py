#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

HERE = Path(__file__).resolve().parent

def run(cmd, check=True, capture=False, env=None):
    print(f"+ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.STDOUT if capture else None,
                          env=env)

def load_dotenv(path: Path) -> dict:
    env = {}
    if not path.exists():
        print(f"[WARN] No se encontró {path}, continúo con entorno del proceso.")
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
        if not m: 
            continue
        k, v = m.group(1), m.group(2)
        # Expande ${VAR} dentro del valor usando lo ya leído
        def repl(m2):
            name = m2.group(1)
            return env.get(name, os.environ.get(name, ""))
        v = re.sub(r"\$\{([^}]+)\}", repl, v)
        env[k] = v
    return env

def ensure_dirs(*paths: Path):
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def check_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return True
        except OSError:
            return False

def must_have(cmd, name):
    if shutil.which(cmd) is None:
        print(f"[ERROR] No se encontró {name} en PATH ({cmd}).")
        sys.exit(2)

def docker_compose_cmd():
    # Usa 'docker compose' si existe, si no 'docker-compose'
    if shutil.which("docker") is not None:
        # Verifica plugin compose
        try:
            run(["docker", "compose", "version"], check=True, capture=True)
            return ["docker", "compose"]
        except Exception:
            pass
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    print("[ERROR] No se encontró ni 'docker compose' ni 'docker-compose'.")
    sys.exit(2)

def cert_present(conf_dir: Path, domain: str) -> bool:
    live = conf_dir / "live" / domain
    return (live / "fullchain.pem").is_file() and (live / "privkey.pem").is_file()

def issue_cert_with_standalone(conf_dir: Path, domain: str, email: str, staging=False, http_port=80, force_renew=False, dry=False):
    """
    Usa certbot en contenedor con --standalone (escucha en :80).
    """
    if not check_port_free(http_port):
        print(f"[INFO] El puerto {http_port} no está libre. Intento liberar el stack para emitir el certificado.")
        # El caller debe haber parado el stack, pero por si acaso:
    else:
        print(f"[OK] Puerto {http_port} libre para certbot standalone.")

    base_cmd = [
        "docker", "run", "--rm",
        "-p", f"{http_port}:80",
        "-v", f"{conf_dir}:/etc/letsencrypt",
        "certbot/certbot:latest",
    ]

    if force_renew and cert_present(conf_dir, domain):
        # Fuerza renovación
        cert_cmd = base_cmd + [
            "renew", "--force-renewal"
        ]
    elif cert_present(conf_dir, domain):
        # Renovación normal
        cert_cmd = base_cmd + ["renew"]
    else:
        # Primera emisión
        cert_cmd = base_cmd + [
            "certonly", "--standalone",
            "--preferred-challenges", "http",
            "-d", domain,
            "-m", email,
            "--agree-tos",
            "--non-interactive"
        ]
        if staging:
            cert_cmd.append("--staging")

    if dry:
        print(f"[DRY] {' '.join(cert_cmd)}")
        return

    print("[STEP] Lanzando certbot (standalone)")
    res = run(cert_cmd, check=False, capture=True)
    print(res.stdout if res.stdout else "")
    if res.returncode != 0:
        print("[ERROR] Certbot devolvió código != 0. Revisa salida anterior.")
        sys.exit(res.returncode)

def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap TLS (Let's Encrypt) + arranque del stack Docker Compose para el bot."
    )
    parser.add_argument("--compose-file", "-f", default=str(HERE / "docker-compose.yml"),
                        help="Ruta a docker-compose.yml (por defecto: ./docker-compose.yml)")
    parser.add_argument("--env-file", default=str(HERE / ".env"),
                        help="Ruta a .env (por defecto: ./.env)")
    parser.add_argument("--staging", action="store_true",
                        help="Usar CA de staging de Let's Encrypt para pruebas.")
    parser.add_argument("--http-port", type=int, default=80,
                        help="Puerto HTTP para el challenge standalone (por defecto 80).")
    parser.add_argument("--skip-renewal", action="store_true",
                        help="No ejecutar certbot (útil si ya tienes el cert).")
    parser.add_argument("--only-renew", action="store_true",
                        help="Solo ejecutar emisión/renovación, no subir el stack.")
    parser.add_argument("--force-renew", action="store_true",
                        help="Fuerza renovación aunque no esté próximo a expirar.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostrar comandos sin ejecutarlos.")
    args = parser.parse_args()

    must_have("docker", "docker")
    compose = docker_compose_cmd()

    env_path = Path(args.env_file)
    env = load_dotenv(env_path)

    domain = env.get("DOMAIN")
    email  = env.get("EMAIL")
    if not domain or not email:
        print("[ERROR] DOMAIN y/o EMAIL no están definidos en .env (o flags).")
        sys.exit(2)

    # Rutas persistentes
    certbot_conf = HERE / "certbot" / "conf"
    certbot_www  = HERE / "certbot" / "www"  # no se usa en standalone, pero lo mantenemos
    ensure_dirs(certbot_conf, certbot_www)

    # Baja el stack si está arriba (para liberar :80 para --standalone)
    print("[STEP] docker compose down (para liberar puertos 80/443)")
    if args.dry_run:
        print(f"[DRY] {' '.join(compose + ['-f', args.compose_file, 'down'])}")
    else:
        run(compose + ["-f", args.compose_file, "down"], check=False)

    # Comprueba puerto 80
    if not check_port_free(args.http_port):
        print(dedent(f"""
        [ERROR] El puerto {args.http_port} NO está libre. 
                Cierra cualquier servicio en {args.http_port} (nginx/apache/otra app) o cambia --http-port.
        """).strip())
        sys.exit(2)

    # Emisión/Renovación
    if not args.skip_renewal:
        issue_cert_with_standalone(
            conf_dir=certbot_conf,
            domain=domain,
            email=email,
            staging=args.staging,
            http_port=args.http_port,
            force_renew=args.force_renew,
            dry=args.dry_run
        )
        # Verifica presencia de ficheros
        if not cert_present(certbot_conf, domain):
            print("[ERROR] No se encuentran fullchain.pem/privkey.pem tras certbot.")
            sys.exit(2)
        print("[OK] Certificado presente en ./certbot/conf/live/{domain}/")
    else:
        print("[INFO] Saltando certbot por --skip-renewal.")

    if args.only_renew:
        print("[DONE] Emisión/Renovación completada. No se arranca el stack (--only-renew).")
        return

    # Arranca el stack completo
    print("[STEP] docker compose up -d")
    if args.dry_run:
        print(f"[DRY] {' '.join(compose + ['-f', args.compose_file, 'up', '-d'])}")
    else:
        run(compose + ["-f", args.compose_file, "up", "-d"], check=True)

    # Tail opcional: muestra cabeceras de salud del proxy y del bot
    print("[TIP] Para seguir logs desde ahora:  docker compose -f {} logs -f --tail=0".format(args.compose_file))
    print("[TIP] Pruebas rápidas:")
    print(f"      curl -I http://{domain}/.well-known/acme-challenge/ping   # si mapeas ping en certbot/www")
    print(f"      curl -I https://{domain}/health")
    print(f"      curl -s -o /dev/null -w \"%{{http_code}}\\n\" -X POST -H \"X-Telegram-Bot-Api-Secret-Token: ${{WEBHOOK_SECRET}}\" https://{domain}/telegram/webhook")

if __name__ == "__main__":
    main()

