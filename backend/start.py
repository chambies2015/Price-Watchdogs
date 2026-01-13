#!/usr/bin/env python3
import os
import subprocess
import sys

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
    
    print("Running database migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False
    )
    
    if result.returncode != 0:
        print("Warning: Migrations failed (this may be normal if tables already exist).")
        print("Attempting to stamp database to current version...")
        stamp_result = subprocess.run(
            [sys.executable, "-m", "alembic", "stamp", "head"],
            check=False
        )
        if stamp_result.returncode == 0:
            print("Database stamped successfully.")
        else:
            print("Warning: Could not stamp database, but continuing...")
    
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

