import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent / "src" / "app_api"
sys.path.insert(0, str(API_ROOT))

os.environ.setdefault("POSTGRES_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
