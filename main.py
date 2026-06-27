import sys
from pathlib import Path

# Add backend directory to path to allow absolute imports of 'app'
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.main import app

__all__ = ["app"]
