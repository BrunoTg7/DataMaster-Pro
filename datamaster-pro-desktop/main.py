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

# Configurar logging centralizado
import config
from src.core.logging_setup import configure_logging
configure_logging(config.LOGS_DIR)

logger = __import__("logging").getLogger(__name__)
logger.info("Inicializando %s v%s", config.APP_NAME, config.APP_VERSION)

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
