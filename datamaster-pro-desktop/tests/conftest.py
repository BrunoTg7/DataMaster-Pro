"""
Conftest — Adiciona o projeto ao sys.path automaticamente.
Substitui TODOS os sys.path.insert espalhados pelos testes.
"""
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao path (datamaster-pro-desktop/)
_root = str(Path(__file__).parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
