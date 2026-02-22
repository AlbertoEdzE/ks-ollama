import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

LOG_DIR = Path("scripts")
LOG_FILE = LOG_DIR / "run.log"
VENV = Path(".venv")

def log(msg: str):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{ts} {msg}\n")
    print(msg, flush=True)

def run(cmd: list[str], cwd: str | None = None, env: dict | None = None, check: bool = False):
    try:
        res = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=check)
        log(f"$ {' '.join(cmd)}")
        if res.stdout:
            for line in res.stdout.splitlines():
                log(line)
        return res.returncode == 0
    except Exception as e:
        log(f"error: {e}")
        return False

def port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def ensure_venv():
    if not VENV.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    pip = str(VENV / "bin" / "pip")
    run([pip, "install", "--upgrade", "pip"])
    run([pip, "install", "-r", "requirements.txt"])

def validate_env(env_name: str):
    defaults = {
        "ENVIRONMENT": "local" if env_name == "dev" else "prod",
        "DB_USER": "app",
        "DB_PASSWORD": "app",
        "DB_HOST": "localhost" if env_name == "dev" else "db",
        "DB_PORT": "5432",
        "DB_NAME": "app",
        "JWT_SECRET": "dev-secret" if env_name == "dev" else os.getenv("JWT_SECRET", ""),
    }
    for k, v in defaults.items():
        os.environ.setdefault(k, v)
    missing = [k for k in ["JWT_SECRET"] if not os.environ.get(k)]
    if env_name == "prod" and missing:
        raise RuntimeError("missing required environment variables: " + ", ".join(missing))

def start_db(env_name: str):
    if env_name == "dev":
        if Path("docker-compose.dev.yml").exists():
            host_port = int(os.environ.get("DB_PORT", "5432"))
            if port_open("127.0.0.1", host_port):
                # If busy, try alternate port
                if host_port == 5432:
                    host_port = 5433
                    os.environ["DB_PORT"] = str(host_port)
                os.environ["DB_PORT_HOST"] = str(host_port)
            else:
                os.environ.setdefault("DB_PORT_HOST", str(host_port))
            run(["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d", "db"])
        target_port = int(os.environ.get("DB_PORT", "5432"))
        for _ in range(60):
            if port_open("127.0.0.1", target_port):
                log("database is ready")
                return
            time.sleep(1)
        # extra readiness: attempt connection if port opened too early
        try:
            import psycopg2
            for _ in range(30):
                try:
                    conn = psycopg2.connect(
                        host="127.0.0.1",
                        port=target_port,
                        user=os.environ.get("DB_USER", "app"),
                        password=os.environ.get("DB_PASSWORD", "app"),
                        dbname=os.environ.get("DB_NAME", "app"),
                    )
                    conn.close()
                    log("database connection verified")
                    return
                except Exception:
                    time.sleep(1)
        except Exception:
            pass
        raise RuntimeError("database did not become ready or accept connections")

def migrate_and_seed():
    bin_py = str(VENV / "bin" / "python")
    alembic_bin = str(VENV / "bin" / "alembic")
    if not Path(alembic_bin).exists():
        raise RuntimeError("alembic not found in virtualenv; dependency installation may have failed")
    ok = run([alembic_bin, "upgrade", "head"], check=True)
    if not ok:
        if os.environ.get("ENVIRONMENT", "local") == "local":
            log("alembic migration failed; continuing with metadata create + seed for local dev")
        else:
            raise RuntimeError("database migration failed")
    run([bin_py, "-m", "app.db.seed"])

def start_api():
    api_port = int(os.environ.get("API_PORT", "8080"))
    if port_open("127.0.0.1", api_port):
        found = None
        for p in range(8080, 8091):
            if not port_open("127.0.0.1", p):
                found = p
                break
        if found is None:
            raise RuntimeError("no free API port in 8080-8090")
        api_port = found
        os.environ["API_PORT"] = str(api_port)
        log(f"api port busy; switching to {api_port}")
    env = os.environ.copy()
    proc = subprocess.Popen(
        [
            str(VENV / "bin" / "python"),
            "-m",
            "gunicorn",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "--bind",
            f"0.0.0.0:{api_port}",
            "app.main:app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    for _ in range(60):
        if port_open("127.0.0.1", api_port):
            log(f"api is ready on :{api_port}")
            break
        time.sleep(1)
    return proc

def start_frontend(env_name: str):
    if env_name == "dev":
        if Path("docker-compose.dev.yml").exists():
            env = os.environ.copy()
            # Avoid starting the backend container; we run backend locally
            run(["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d", "--no-deps", "frontend"], env=env)
        frontend_port = int(os.environ.get("FRONTEND_PORT", "5173"))
        for _ in range(60):
            if port_open("127.0.0.1", frontend_port):
                log(f"frontend is ready on :{frontend_port}")
                return
            time.sleep(1)
        raise RuntimeError("frontend did not become ready")

def health_checks():
    try:
        import httpx
        api_port = int(os.environ.get("API_PORT", "8080"))
        r1 = httpx.get(f"http://127.0.0.1:{api_port}/healthz", timeout=5)
        r2 = httpx.get(f"http://127.0.0.1:{api_port}/readyz", timeout=5)
        ok1 = r1.status_code == 200
        ok2 = r2.status_code == 200
        if not (ok1 and ok2):
            raise RuntimeError("health checks failed")
        log("health checks passed")
    except Exception as e:
        raise RuntimeError(f"health checks error: {e}")

def login_check():
    try:
        import httpx
        api_port = int(os.environ.get("API_PORT", "8080"))
        payload = {"username": "admin@example.com", "password": os.environ.get("ADMIN_BOOTSTRAP_PASSWORD", "admin")}
        r = httpx.post(f"http://127.0.0.1:{api_port}/auth/login", json=payload, timeout=10)
        if r.status_code != 200:
            raise RuntimeError(f"login check failed with status {r.status_code}: {r.text}")
        token = r.json().get("access_token")
        if not token:
            raise RuntimeError("login check did not return access_token")
        log("login check passed for admin@example.com")
    except Exception as e:
        raise RuntimeError(f"login verification error: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev", "prod"], default="dev")
    parser.add_argument("--no-frontend", action="store_true")
    parser.add_argument("--no-backend", action="store_true")
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()
    try:
        log("startup sequence initiated")
        ensure_venv()
        validate_env(args.env)
        # Configure dynamic ports and frontend API base
        # Pre-select API port to keep frontend in sync
        if not os.environ.get("API_PORT"):
            chosen = None
            for p in (8080, 8081, 8082, 8083):
                if not port_open("127.0.0.1", p):
                    chosen = p
                    break
            if chosen is None:
                chosen = 8084
            os.environ["API_PORT"] = str(chosen)
        api_port = os.environ.get("API_PORT", "8080")
        if args.env == "dev":
            os.environ.setdefault("ADMIN_BOOTSTRAP_PASSWORD", "admin")
            os.environ.setdefault("ADMIN_BOOTSTRAP_PASSWORD_FORCE", "1")
        # Pick a frontend port (5173 or 5174) if 5173 is busy
        fe_port = 5173
        if port_open("127.0.0.1", fe_port):
            alt = 5174
            if not port_open("127.0.0.1", alt):
                fe_port = alt
        os.environ["FRONTEND_PORT"] = str(fe_port)
        # Ensure Vite uses correct API base in served JavaScript
        os.environ["VITE_API_BASE"] = f"http://localhost:{api_port}"
        if not args.no_backend:
            start_db(args.env)
            migrate_and_seed()
            api_proc = start_api()
            health_checks()
            login_check()
        else:
            api_proc = None
        if not args.no_frontend:
            start_frontend(args.env)
        log(f"system started at http://127.0.0.1:{os.environ.get('API_PORT', '8080')} and http://127.0.0.1:{os.environ.get('FRONTEND_PORT', '5173')}")
        if args.open_browser:
            try:
                import webbrowser
                webbrowser.open(f"http://127.0.0.1:{os.environ.get('API_PORT', '8080')}/docs")
                webbrowser.open(f"http://127.0.0.1:{os.environ.get('FRONTEND_PORT', '5173')}")
            except Exception as e:
                log(f"failed to open browser: {e}")
        if api_proc:
            for line in api_proc.stdout:
                if line:
                    log(line.rstrip())
    except Exception as e:
        log(f"startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
