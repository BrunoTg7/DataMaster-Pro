"""
Auto-Update Checker - Verifica e baixa atualizações automaticamente
"""
import os
import sys
import json
import requests
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict
import threading


class UpdateChecker:
    """Sistema de verificação e instalação de atualizações"""

    def __init__(self, current_version: str, update_url: str = None):
        self.current_version = current_version
        self.update_url = update_url or os.getenv("UPDATE_URL", "")
        self.update_info: Optional[Dict] = None

    def check_for_updates(self) -> Dict:
        """
        Verifica se há atualização disponível.
        Returns: {has_update: bool, version: str, download_url: str, changelog: str}
        """
        if not self.update_url:
            return {"has_update": False, "reason": "URL de update não configurada"}

        try:
            response = requests.get(self.update_url, timeout=10)
            if response.status_code != 200:
                return {"has_update": False, "reason": "Erro ao buscar atualizações"}

            data = response.json()
            latest_version = data.get("version", "")

            if self._is_newer_version(latest_version, self.current_version):
                return {
                    "has_update": True,
                    "version": latest_version,
                    "download_url": data.get("download_url", ""),
                    "changelog": data.get("changelog", ""),
                    "file_size": data.get("file_size", 0),
                    "mandatory": data.get("mandatory", False)
                }

            return {"has_update": False, "reason": "Você já tem a última versão"}

        except Exception as e:
            return {"has_update": False, "reason": f"Erro: {str(e)}"}

    def _is_newer_version(self, new: str, current: str) -> bool:
        """Compara versões"""
        try:
            new_parts = [int(x) for x in new.split('.')]
            cur_parts = [int(x) for x in current.split('.')]

            for i in range(max(len(new_parts), len(cur_parts))):
                n = new_parts[i] if i < len(new_parts) else 0
                c = cur_parts[i] if i < len(cur_parts) else 0
                if n > c:
                    return True
                elif n < c:
                    return False
            return False
        except:
            return False

    def download_and_install(self, download_url: str, on_progress=None, on_complete=None):
        """Baixa e instala a atualização em background"""

        def worker():
            try:
                # Baixar installer
                response = requests.get(download_url, stream=True)
                total_size = int(response.headers.get('content-length', 0))

                with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
                    temp_file = f.name
                    downloaded = 0

                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if on_progress and total_size:
                                progress = int((downloaded / total_size) * 100)
                                on_progress(progress)

                # Executar installer (silencioso)
                if on_complete:
                    on_complete(temp_file, None)

            except Exception as e:
                if on_complete:
                    on_complete(None, str(e))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()


def check_update_on_start():
    """Função para chamar ao iniciar a aplicação"""
    try:
        config = __import__('config', fromlist=['APP_VERSION', 'ENVIRONMENT'])
        current_version = getattr(config, 'APP_VERSION', '1.0.0')

        checker = UpdateChecker(current_version)
        result = checker.check_for_updates()

        if result.get("has_update"):
            return {
                "available": True,
                "version": result.get("version"),
                "changelog": result.get("changelog", ""),
                "mandatory": result.get("mandatory", False)
            }
    except:
        pass

    return {"available": False}


# ============================================================
# ARQUIVO DE CONFIGURAÇÃO DE UPDATE (JSON)
# ============================================================
# O servidor deve retornar um JSON como este:
"""
{
    "version": "1.1.0",
    "download_url": "https://seu-servidor.com/releases/DataMaster-Pro-1.1.0.exe",
    "changelog": "- Nova ferramenta de comissões\n- Correções de bugs",
    "file_size": 52428800,
    "mandatory": false
}
"""