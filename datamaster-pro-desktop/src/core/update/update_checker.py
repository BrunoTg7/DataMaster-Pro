"""
Auto-Update Checker Pro v3.7 - Final Release
Correção de sincronização entre Core e GUI (has_update -> available).
"""
import os
import sys
import threading
import logging
from typing import Optional, Dict
from supabase import create_client

logger = logging.getLogger(__name__)

class UpdateChecker:
    """Sistema de atualização nativo via Supabase"""

    def __init__(self, current_version: str):
        self.current_version = current_version
        import config
        self._url = config._u0
        self._key = config._r1()

    def check_for_updates(self) -> Dict:
        logger.info(f"Verificando atualizações... (Local: {self.current_version})")

        if not self._url or not self._key:
            return {"has_update": False}

        try:
            _c = create_client(self._url, self._key)
            response = _c.table("check_updates").select("*").order("id", desc=True).limit(1).execute()

            if not response.data:
                return {"has_update": False}

            latest_data = response.data[0]
            if not isinstance(latest_data, dict):
                return {"has_update": False}
            latest_version = latest_data.get("versao_disponivel", "")
            download_url = latest_data.get("url_download", "")

            sha256 = (
                latest_data.get("sha256")
                or latest_data.get("sha256_checksum")
                or latest_data.get("checksum_sha256")
                or latest_data.get("hash_sha256")
                or latest_data.get("hash")
                or ""
            )

            if self._is_newer_version(latest_version, self.current_version):
                logger.info(f"UPDATE DETECTADO: {latest_version}")
                return {
                    "has_update": True,
                    "version": latest_version,
                    "download_url": download_url,
                    "sha256": sha256,
                    "changelog": latest_data.get("changelog", "Melhorias de estabilidade."),
                    "mandatory": latest_data.get("mandatory", False)
                }

            return {"has_update": False}

        except Exception as e:
            logger.error(f"Erro ao verificar atualizações: {e}")
            return {"has_update": False}

    def _is_newer_version(self, new: str, current: str) -> bool:
        try:
            new_parts = [int(x) for x in str(new).split('.')]
            cur_parts = [int(x) for x in str(current).split('.')]
            for i in range(max(len(new_parts), len(cur_parts))):
                n = new_parts[i] if i < len(new_parts) else 0
                c = cur_parts[i] if i < len(cur_parts) else 0
                if n > c: return True
                elif n < c: return False
            return False
        except Exception: return False

    def download_and_install(self, download_url: str, expected_sha256: str = None, on_progress=None, on_complete=None):
        def worker():
            import hashlib
            import requests, tempfile
            try:
                response = requests.get(download_url, stream=True, timeout=60)
                total_size = int(response.headers.get('content-length', 0))
                sha256_hash = hashlib.sha256()
                with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
                    temp_file = f.name
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            sha256_hash.update(chunk)
                            downloaded += len(chunk)
                            if on_progress and total_size:
                                on_progress(int((downloaded / total_size) * 100))
                if expected_sha256:
                    actual = sha256_hash.hexdigest().lower()
                    if actual != expected_sha256.lower():
                        os.unlink(temp_file)
                        if on_complete: on_complete(None, f"SHA-256 mismatch: esperado {expected_sha256}, obtido {actual}")
                        return
                if on_complete: on_complete(temp_file, None)
            except Exception as e:
                if on_complete: on_complete(None, str(e))
        threading.Thread(target=worker, daemon=True).start()

def check_update_on_start():
    """Função padronizada para a GUI"""
    try:
        import config
        checker = UpdateChecker(config.APP_VERSION)
        result = checker.check_for_updates()
        # Sincroniza o nome do campo para a GUI
        result["available"] = result.get("has_update", False)
        return result
    except Exception:
        return {"available": False}