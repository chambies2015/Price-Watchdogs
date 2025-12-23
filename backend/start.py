#!/usr/bin/env python3
import os
import subprocess
import sys

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
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
    
    print("Starting FastAPI application...")
    port = os.environ.get("PORT", "8000")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port]
    )

