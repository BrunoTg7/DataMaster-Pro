"""
Configurações Globais - DataMaster Pro Desktop
"""

import os
import sys
from pathlib import Path
from enum import Enum

# ==================== CARREGAR .ENV MANUALMENTE SE NECESSÁRIO ====================
def _ensure_env_loaded():
    """Garante que variáveis de ambiente estão carregadas"""
    
    # Se já tem SUPABASE_URL, pular
    if os.getenv("SUPABASE_URL"):
        return
    
    # Tentar localizar .env
    paths = [
        Path.cwd() / ".env",
        Path(__file__).parent / ".env",
        Path(sys.executable).parent / ".env",
    ]
    
    for env_path in paths:
        if env_path.exists():
            # Carregar manualmente
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                os.environ[key.strip()] = value.strip()
            except:
                pass
            break

_ensure_env_loaded()

# ==================== AMBIENTE ====================
ENV = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENV == "production"

# ==================== APP ====================
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_NAME = os.getenv("APP_NAME", "DataMaster Pro")

# ==================== AUTO-UPDATE ====================
UPDATE_URL = os.getenv("UPDATE_URL", "")
UPDATE_CHECK_ON_START = os.getenv("UPDATE_CHECK_ON_START", "true").lower() == "true"

# ==================== SUPABASE ====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# ==================== SCRAPERAPI ====================
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "")

# Validação
if not SUPABASE_URL:
    raise ValueError(
        "⚠️  ERRO: supabase_url não foi carregado!\n"
        "Verifique se o arquivo .env existe e contém SUPABASE_URL"
    )

# ==================== INTERFACE ====================
THEME = os.getenv("THEME", "dark")
WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))
WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "800"))

# ==================== CORES ====================
class Colors:
    # Tema Escuro (Desktop)
    DARK = {
        "BACKGROUND": "#09090B",
        "CARD": "#18181B",
        "BORDER": "#27272A",
        "PRIMARY": "#d48214",
        "PRIMARY_HOVER": "#b5690f",
        "ALERT": "#EF4444",
        "TEXT_PRIMARY": "#FAFAFA",
        "TEXT_SECONDARY": "#A1A1AA"
    }
    
    # Tema Claro (Web)
    LIGHT = {
        "BACKGROUND": "#FAFAFA",
        "CARD": "#FFFFFF",
        "BORDER": "#E5E7EB",
        "PRIMARY": "#d48214",
        "PRIMARY_HOVER": "#b5690f",
        "ALERT": "#EF4444",
        "TEXT_PRIMARY": "#111827",
        "TEXT_SECONDARY": "#6B7280"
    }
    
    @staticmethod
    def update_from_theme(theme_name: str):
        """Atualiza as cores com base no tema"""
        theme = Colors.DARK if theme_name == "dark" else Colors.LIGHT if theme_name == "light" else Colors.DARK
        Colors.BACKGROUND = theme["BACKGROUND"]
        Colors.CARD = theme["CARD"]
        Colors.BORDER = theme["BORDER"]
        Colors.PRIMARY = theme["PRIMARY"]
        Colors.PRIMARY_HOVER = theme["PRIMARY_HOVER"]
        Colors.ALERT = theme["ALERT"]
        Colors.TEXT_PRIMARY = theme["TEXT_PRIMARY"]
        Colors.TEXT_SECONDARY = theme["TEXT_SECONDARY"]

# Inicializar com tema padrão
Colors.update_from_theme(THEME)

# ==================== DIRETÓRIOS ====================
HOME_DIR = os.path.expanduser("~")
APP_DATA_DIR = os.path.join(HOME_DIR, ".datamaster")
DB_PATH = os.path.join(APP_DATA_DIR, "datamaster.db")
CACHE_DIR = os.path.join(APP_DATA_DIR, "cache")
LOGS_DIR = os.path.join(APP_DATA_DIR, "logs")

# Criar diretórios se não existirem
os.makedirs(APP_DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ==================== PLANOS ====================
class PlanType(Enum):
    GRATIS = "gratis"
    PRO = "pro"
    ENTERPRISE = "enterprise"

PLAN_LIMITS = {
    PlanType.GRATIS: {
        "name": "Grátis",
        "tagline": "Perfeito para validar a potência das ferramentas",
        "max_lines_month": 1200,
        "max_execs_month": 15,
        "tools_limit": {
            "consolidador": {"max_per_exec": 600, "max_execs": 3},
            "categorizador": {"max_per_exec": 600, "max_execs": 3},
            "orcamentos": {"max_per_exec": 15, "max_execs": 5},
            "conciliador": {"max_per_exec": None, "max_execs": 3},
            "minerador": {"max_per_exec": 10, "max_execs": 2},
            "validador_links": {"max_per_exec": 20, "max_execs": 2},
            "extrator_reviews": {"max_per_exec": 10, "max_execs": 2},
            "calculadora_lucratividade": {"max_per_exec": 10, "max_execs": 2},
            "analista_tendencias": {"max_per_exec": 5, "max_execs": 2},
            "data_sanitizer": {"max_per_exec": 500, "max_execs": 5},
            "conversor_ocr": {"max_per_exec": 10, "max_execs": 2},
            "gerador_laudos": {"max_per_exec": 10, "max_execs": 3},
            "comissoes": {"max_per_exec": 100, "max_execs": 10},
        },
        "tools": ["consolidador", "categorizador", "orcamentos", "minerador", "conciliador", "validador_links", "extrator_reviews", "calculadora_lucratividade", "analista_tendencias", "data_sanitizer", "conversor_ocr", "gerador_laudos", "comissoes"],
        "watermark": True,
        "price": 0.00
    },
    PlanType.PRO: {
        "name": "Pro",
        "tagline": "Para profissionais que buscam performance máxima",
        "max_lines": None,
        "tools": ["all"],
        "watermark": False,
        "price": 49.90,
        "annual_price": 359.28
    },
    PlanType.ENTERPRISE: {
        "name": "Enterprise",
        "tagline": "Solução sob medida para grandes empresas",
        "max_lines": None,
        "tools": ["all"],
        "watermark": False,
        "price": None
    }
}

# ==================== SINCRONIZAÇÃO ====================
SYNC_INTERVAL_MS = int(os.getenv("SYNC_INTERVAL_MS", "30000"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_MS = int(os.getenv("RETRY_DELAY_MS", "5000"))

# ==================== FERRAMENTAS ====================
TOOLS = {
    "consolidador": {
        "name": "Consolidador",
        "description": "Une múltiplas planilhas em uma estrutura única",
        "icon": "merge"
    },
    "categorizador": {
        "name": "Categorizador",
        "description": "Classifica transações por palavras-chave",
        "icon": "tag"
    },
    "orcamentos": {
        "name": "Orçamentos",
        "description": "Preenche templates de PDF em massa",
        "icon": "file"
    },
    "minerador": {
        "name": "Minerador",
        "description": "Captura preços de sites concorrentes",
        "icon": "globe"
    },
    "conciliador": {
        "name": "Conciliador",
        "description": "Cruza extratos com planilhas de vendas",
        "icon": "check"
    },
    "validador_links": {
        "name": "Validador de Links",
        "description": "Verifica se links estão ativos e produtos disponíveis",
        "icon": "link"
    },
    "extrator_reviews": {
        "name": "Extrator de Reviews",
        "description": "Extrai e analisa sentimento de reviews de marketplaces",
        "icon": "star"
    },
    "calculadora_lucratividade": {
        "name": "Calculadora de Lucratividade",
        "description": "Calcula margem de lucro e identifica oportunidades de arbitragem",
        "icon": "calculator"
    },
    "analista_tendencias": {
        "name": "Analista de Tendências",
        "description": "Identifica produtos trending em nichos específicos",
        "icon": "trending"
    },
    "data_sanitizer": {
        "name": "Data Sanitizer",
        "description": "Limpa e normaliza dados de planilhas (CPF, CNPJ, nomes, endereços)",
        "icon": "cleaning"
    },
    "conversor_ocr": {
        "name": "Conversor OCR",
        "description": "Extrai tabelas de imagens e PDFs escaneados para Excel",
        "icon": "scan"
    },
    "gerador_laudos": {
        "name": "Gerador de Laudos",
        "description": "Gera laudos de conformidade cruzando extratos com notas fiscais",
        "icon": "document"
    },
    "comissoes": {
        "name": "Comissões",
        "description": "Calcule comissões de vendedores e gere relatórios individuais em PDF",
        "icon": "percent"
    }
}

# ==================== WEB SCRAPING (2024/2025) ====================
# Chrome (Windows)
CHROME_WINDOWS = [
   # Chrome 124 — mais recente
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Windows 11
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]
 
# ==================== CHROME (MAC) ====================
CHROME_MAC = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Apple Silicon (arm64)
    "Mozilla/5.0 (Macintosh; ARM Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; ARM Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

CHROME_LINUX = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# Firefox
FIREFOX_ALL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

# Safari & Edge
OTHER_DESKTOP = [
     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge no Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

# Mobile
MOBILE_ALL = [
   # iPhone — Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    # iPhone — Chrome
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.88 Mobile/15E148 Safari/604.1",
    # iPad — Safari
    "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    # Chrome (Android) — vários modelos
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; moto g(60)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36",
    # Genérico (menos rastreável)
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    # Samsung Browser
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/24.0 Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",
]

# Bot-Friendly (Útil para sites que permitem indexadores)
BOT_FRIENDLY = [
     # Googlebot
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/124.0.6367.60 Safari/537.36",
    # Bingbot
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    # DuckDuckBot
    "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
    # Slurp (Yahoo)
    "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
]

# Lista Unificada
USER_AGENTS = CHROME_WINDOWS + CHROME_MAC + CHROME_LINUX + FIREFOX_ALL + OTHER_DESKTOP + MOBILE_ALL

# Tipos para seleção estratégica
_UA_TYPES = {
    "desktop":      CHROME_WINDOWS + CHROME_MAC + CHROME_LINUX + FIREFOX_ALL + OTHER_DESKTOP,
    "mobile":       MOBILE_ALL,
    "chrome":       CHROME_WINDOWS + CHROME_MAC,
    "firefox":      FIREFOX_ALL,
    "bot_friendly": BOT_FRIENDLY,
    "all":          USER_AGENTS,
}

def get_random_ua(ua_type: str = "desktop") -> str:
    """Retorna um User Agent aleatório do tipo especificado"""
    import random
    pool = _UA_TYPES.get(ua_type, USER_AGENTS)
    return random.choice(pool)

def get_ua_by_type(ua_type: str) -> list:
    """Retorna a lista completa de UAs de um tipo"""
    return _UA_TYPES.get(ua_type, USER_AGENTS)
