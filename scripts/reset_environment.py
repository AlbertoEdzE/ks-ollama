import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

LOG_DIR = Path("scripts")
LOG_FILE = LOG_DIR / "reset.log"

def log(msg: str):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{ts} {msg}\n")
    print(msg)

def run(cmd: list[str], cwd: str | None = None, check: bool = False):
    try:
        res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=check)
        log(f"$ {' '.join(cmd)}")
        if res.stdout:
            for line in res.stdout.splitlines():
                log(line)
        return res.returncode == 0
    except Exception as e:
        log(f"error: {e}")
        return False

def confirm_or_exit(yes: bool):
    if yes:
        return
    ans = input("This will irreversibly reset the environment. Type YES to continue: ")
    if ans.strip().upper() != "YES":
        print("Aborted")
        sys.exit(1)

def stop_services(env: str):
    compose_file = "docker-compose.dev.yml" if env == "dev" else "docker-compose.prod.yml"
    if Path(compose_file).exists():
        run(["docker", "compose", "-f", compose_file, "down", "-v"])
    for p in ["gunicorn", "uvicorn"]:
        run(["pkill", "-f", p])

def reset_db_by_sqlalchemy():
    try:
        os.environ.setdefault("ENVIRONMENT", "local")
        from app.db.session import engine
        from app.db.base import Base
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        log("database schema reset")
        return True
    except Exception as e:
        log(f"database reset skipped: {e}")
        return False

def remove_paths(paths: list[Path]):
    for p in paths:
        if p.is_dir():
            try:
                shutil.rmtree(p, ignore_errors=True)
                log(f"removed dir {p}")
            except Exception as e:
                log(f"failed to remove dir {p}: {e}")
        elif p.exists():
            try:
                p.unlink()
                log(f"removed file {p}")
            except Exception as e:
                log(f"failed to remove file {p}: {e}")

def reset_configs():
    env_path = Path(".env")
    content = [
        "ENVIRONMENT=local",
        "DB_USER=app",
        "DB_PASSWORD=app",
        "DB_HOST=localhost",
        "DB_PORT=5432",
        "DB_NAME=app",
        "JWT_SECRET=dev-secret",
        "OLLAMA_BASE_URL=",
        "",
    ]
    try:
        env_path.write_text("\n".join(content))
        log("configs reset to defaults: .env")
    except Exception as e:
        log(f"failed to reset configs: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev", "prod"], default="dev")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    confirm_or_exit(args.yes)
    log("starting environment reset")
    stop_services(args.env)
    reset_db_by_sqlalchemy()
    caches = [
        Path(".pytest_cache"),
        Path(".mypy_cache"),
        Path(".ruff_cache"),
        Path("frontend/node_modules"),
        Path("build"),
        Path("dist"),
        Path("__pycache__"),
    ]
    tmp_globs = ["**/__pycache__", "**/*.pyc", "**/*.pyo", "logs"]
    remove_paths(caches)
    for pattern in tmp_globs:
        for p in Path(".").glob(pattern):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
                log(f"removed dir {p}")
            elif p.exists():
                p.unlink(missing_ok=True)
                log(f"removed file {p}")
    reset_configs()
    log("environment reset completed")

if __name__ == "__main__":
    main()
