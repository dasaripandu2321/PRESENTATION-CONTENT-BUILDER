import sys
import os
from pathlib import Path

# Add project root to sys.path so 'app' package is discoverable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure Vercel environment flags
os.environ["VERCEL"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOOP_TELEMETRY"] = "True"

from app.main import app

# Export FastAPI app as ASGI handler for Vercel
handler = app
