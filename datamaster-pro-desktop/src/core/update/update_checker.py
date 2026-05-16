"""
Auto-Update Checker Pro v3.7 - Final Release
Correção de sincronização entre Core e GUI (has_update -> available).
"""
import os
import sys
import threading
from typing import Optional, Dict
from supabase import create_client

class UpdateChecker:
    """Sistema de atualização nativo via Supabase"""

    def __init__(self, current_version: str):
        self.current_version = current_version
        import config
        self.supabase_url = config.SUPABASE_URL
        self.supabase_key = config.SUPABASE_ANON_KEY

    def check_for_updates(self) -> Dict:
        print(f"\n[UPDATE] 🔍 Verificando... (Local: {self.current_version})", flush=True)
        
        if not self.supabase_url or not self.supabase_key:
            return {"has_update": False}

        try:
            supabase = create_client(self.supabase_url, self.supabase_key)
            response = supabase.table("check_updates").select("*").order("id", desc=True).limit(1).execute()
            
            if not response.data:
                return {"has_update": False}

            latest_data = response.data[0]
            latest_version = latest_data.get("versao_disponivel", "")
            download_url = latest_data.get("url_download", "")

            if self._is_newer_version(latest_version, self.current_version):
                print(f"[UPDATE] 🔥 UPDATE DETECTADO: {latest_version}", flush=True)
                return {
                    "has_update": True,
                    "version": latest_version,
                    "download_url": download_url,
                    "changelog": latest_data.get("changelog", "Melhorias de estabilidade."),
                    "mandatory": latest_data.get("mandatory", False)
                }

            return {"has_update": False}

        except Exception as e:
            print(f"[UPDATE] 🛑 Erro: {str(e)}", flush=True)
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
        except: return False

    def download_and_install(self, download_url: str, on_progress=None, on_complete=None):
        def worker():
            import requests, tempfile
            try:
                response = requests.get(download_url, stream=True, timeout=60)
                total_size = int(response.headers.get('content-length', 0))
                with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
                    temp_file = f.name
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if on_progress and total_size:
                                on_progress(int((downloaded / total_size) * 100))
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
    except:
        return {"available": False}