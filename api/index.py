import os
import sys

# Ensure repository root is in sys.path for Vercel serverless runtime
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.environ["PYTHONPATH"] = ROOT_DIR

from apps.backend.app.main import app
