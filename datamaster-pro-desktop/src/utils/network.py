"""
Network utilities - Connection checker
"""
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def check_internet_connection(timeout: int = 3) -> bool:
    """Verifica se há conexão com a internet"""
    try:
        response = requests.get("https://www.google.com", timeout=timeout)
        return response.status_code == 200
    except Exception:
        try:
            response = requests.get("https://google.com.br", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False


def check_supabase_connection(timeout: int = 5) -> bool:
    """Verifica se o Supabase está acessível"""
    try:
        response = requests.get(
            f"{config.SUPABASE_URL}/rest/v1/",
            headers={"apikey": config.SUPABASE_ANON_KEY},
            timeout=timeout
        )
        return response.status_code in [200, 401]
    except Exception:
        return False