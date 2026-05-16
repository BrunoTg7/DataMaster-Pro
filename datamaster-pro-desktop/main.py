"""
DataMaster Pro - Desktop Application Entry Point

Main module que inicializa a aplicação com CustomTkinter
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ==================== CARREGAR .ENV ====================
def load_environment():
    """Carrega .env do local correto independente de instalação"""
    
    # Tentar diferentes caminhos
    paths_to_try = [
        Path.cwd() / ".env",  # Diretório atual
        Path(__file__).parent / ".env",  # Mesmo diretório do main.py
        Path(__file__).parent.parent / ".env",  # Diretório pai
        Path(sys.executable).parent / ".env",  # Diretório do executável (instalado)
    ]
    
    # Procurar arquivo .env
    env_path = None
    for path in paths_to_try:
        if path.exists():
            env_path = path
            break
    
    # Carregar
    if env_path:
        load_dotenv(env_path)
    else:
        # Fallback: carregar do diretório atual
        load_dotenv()

load_environment()

# Importar a classe principal da aplicação
from src.gui.app import DataMasterApp

def main():
    """
    Função principal - inicia a aplicação desktop
    """
    app = DataMasterApp()
    app.run()

if __name__ == "__main__":
    main()
