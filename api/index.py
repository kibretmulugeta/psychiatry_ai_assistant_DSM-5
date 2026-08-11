import os
import sys

# Ensure repository root is in sys.path for Vercel serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.environ["PYTHONPATH"] = ROOT_DIR

from apps.backend.app.main import app as fastapi_app

async def app(scope, receive, send):
    """ASGI entrypoint for Vercel Serverless Functions with prefix normalization."""
    if scope.get("type") in ("http", "websocket"):
        path = scope.get("path", "/")
        if path.startswith("/api/index.py"):
            scope["path"] = path.replace("/api/index.py", "", 1) or "/"
        elif path.startswith("/api/index"):
            scope["path"] = path.replace("/api/index", "", 1) or "/"
    await fastapi_app(scope, receive, send)
