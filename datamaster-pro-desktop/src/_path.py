"""
Path helper — resolve sys.path para módulos src/.
Use: from src._path import ensure_path; ensure_path()
"""
import sys
import os
from pathlib import Path


def ensure_path():
    """Garante que a raiz do projeto está no sys.path."""
    root = str(Path(__file__).parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
