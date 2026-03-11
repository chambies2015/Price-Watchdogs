#!/usr/bin/env python3
import os
import subprocess
import sys
import time


def _is_truthy(value):
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if not os.environ.get("DOCKER_BUILD"):
        print("Installing Playwright browsers...")
        playwright_result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False
        )
        if playwright_result.returncode != 0:
            print("Warning: Playwright browser install failed, but continuing...")
    else:
        print("Skipping Playwright install (already done in Docker image)")
    
    if _is_truthy(os.environ.get("MAINTENANCE_MODE")):
        print("MAINTENANCE_MODE enabled: skipping migrations and admin setup.")
    elif _is_truthy(os.environ.get("RUN_MIGRATIONS")) and not _is_truthy(os.environ.get("SKIP_MIGRATIONS")):
        print("Running database migrations...")
        last_rc = 1
        for attempt in range(1, 7):
            result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=False)
            last_rc = result.returncode
            if last_rc == 0:
                break
            if attempt < 7:
                time.sleep(min(2 ** attempt, 15))
        if last_rc != 0:
            sys.exit(last_rc)
        print("Setting up admin account...")
        admin_result = subprocess.run(
            [sys.executable, "scripts/auto_setup_admin.py"],
            check=False
        )
        if admin_result.returncode != 0:
            print("Warning: Admin setup failed, but continuing...")
    
    print("Starting FastAPI application...")
    port = os.environ.get("PORT", "8000")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port]
    )

