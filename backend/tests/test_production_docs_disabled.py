"""Verifies /docs, /redoc, and /openapi.json are all disabled when
APP_ENV=production and ENABLE_DOCS is not set.

This needs a fresh process: `backend.main`'s FastAPI `app` is constructed
once at import time from `settings` at that moment, and the rest of this
test suite already imports it in development mode (see conftest.py). We
spawn a short-lived subprocess with production-mode environment variables so
this test doesn't disturb the shared `app` instance the other tests depend on.
"""
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_docs_and_openapi_disabled_in_production(tmp_path):
    # Run with cwd=tmp_path (not the repo root) so the subprocess's
    # `sqlite:///./test.db` (hardcoded relative path in backend/database.py
    # under TESTING mode) resolves inside tmp_path instead of colliding with
    # the main pytest session's own ./test.db at the repo root, which could
    # otherwise be read/written concurrently by both processes.
    script = textwrap.dedent(
        f"""
        import os
        os.environ["TESTING"] = "True"
        os.environ["APP_ENV"] = "production"
        os.environ["ADMIN_PASSWORD"] = "a-sufficiently-strong-password-123"
        os.environ["SECRET_KEY"] = "a-production-strength-secret-key-that-is-long-enough"
        os.environ["DB_PASSWORD"] = "irrelevant-in-sqlite-testing-mode"
        os.environ["ALLOWED_ORIGINS"] = "https://example.com"
        os.environ.pop("ENABLE_DOCS", None)

        from fastapi.testclient import TestClient
        from backend.main import app

        result = {{
            "docs_url": app.docs_url,
            "redoc_url": app.redoc_url,
            "openapi_url": app.openapi_url,
        }}

        with TestClient(app) as client:
            result["docs_status"] = client.get("/docs").status_code
            result["redoc_status"] = client.get("/redoc").status_code
            result["openapi_status"] = client.get("/openapi.json").status_code

        import json as _json
        print(_json.dumps(result))
        """
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
        timeout=60,
    )
    assert proc.returncode == 0, f"subprocess failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"

    output_line = proc.stdout.strip().splitlines()[-1]
    result = json.loads(output_line)

    assert result["docs_url"] is None
    assert result["redoc_url"] is None
    assert result["openapi_url"] is None
    assert result["docs_status"] == 404
    assert result["redoc_status"] == 404
    assert result["openapi_status"] == 404
