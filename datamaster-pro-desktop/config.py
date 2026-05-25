# DataMaster Pro - Global Configuration

import os
from enum import Enum
import sys
from dotenv import load_dotenv

# Carrega .env se existir
load_dotenv()

# ==================== AMBIENTE ====================
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# ==================== APP ====================
APP_NAME = os.getenv("APP_NAME", "DataMaster Pro")
APP_VERSION = os.getenv("APP_VERSION", "1.4.9")
THEME = os.getenv("THEME", "dark")
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SYNC_INTERVAL_MS = 30000

# ==================== DIRETÓRIOS ====================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    USER_DATA = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'DataMaster Pro')
    os.makedirs(USER_DATA, exist_ok=True)
    LOGS_DIR = os.path.join(USER_DATA, "logs")
    DB_PATH = os.path.join(USER_DATA, "datamaster.db")
    CACHE_DIR = os.path.join(USER_DATA, "cache")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    DB_PATH = os.path.join(BASE_DIR, "datamaster.db")

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
APP_DATA_DIR = USER_DATA if getattr(sys, 'frozen', False) else BASE_DIR
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Garante que diretórios existam
for d in [LOGS_DIR, CACHE_DIR, OUTPUT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

# ==================== SUPABASE ====================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aytpuefpisvmlxmqkbfm.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ==================== CRIPTOGRAFIA ====================
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# ==================== SCRAPERAPI ====================
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "")

# ==================== ESTADO DE SESSÃO ====================
SESSION_UPDATE_CHECKED = False
LAST_UPDATE_DATA = None
SESSION_BANNER_SHOWN = False

# Validação
if not SUPABASE_URL:
    raise ValueError(
        "ERRO: SUPABASE_URL não foi carregado!\n"
        "Verifique se o arquivo .env existe e contém SUPABASE_URL"
    )

if not SUPABASE_ANON_KEY:
    print("AVISO: SUPABASE_ANON_KEY não configurada no .env — autenticação e sincronia podem falhar.")

# ==================== PLANOS E LIMITES ====================
class PlanType(Enum):
    GRATIS = "gratis"
    PRO = "pro"
    ENTERPRISE = "enterprise"

PLAN_LIMITS = {
    PlanType.GRATIS: {
        "max_lines_month": 1200,
        "max_execs_month": 15,
        "tools": ["consolidador", "categorizador", "orcamentos", "minerador", "conciliador", "conversor_ocr", "validador_links", "calculadora_lucratividade", "analista_tendencias", "comissoes"],
        "tools_limit": {
            "consolidador": {"max_per_exec": 600, "max_execs": 5},
            "categorizador": {"max_per_exec": 600, "max_execs": 5},
            "orcamentos": {"max_per_exec": 15, "max_execs": 3},
            "minerador": {"max_per_exec": 15, "max_execs": 2},
            "conciliador": {"max_execs": 2},
            "conversor_ocr": {"max_per_exec": 10, "max_execs": 3},
            "validador_links": {"max_per_exec": 20, "max_execs": 3},
            "calculadora_lucratividade": {"max_execs": 3},
            "analista_tendencias": {"max_per_exec": 5, "max_execs": 3},
            "comissoes": {"max_per_exec": 20, "max_execs": 3},
        }
    },
    PlanType.PRO: {
        "max_lines_month": 999999,
        "max_execs_month": 999,
        "tools": "all"
    }
}

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
    "conversor_ocr": {
        "name": "Conversor OCR",
        "description": "Extrai tabelas de imagens e PDFs escaneados para Excel",
        "icon": "scan",
        "status": "coming_soon",
        "features": ["Suporte a PDF/Imagens", "Extração de Tabelas", "Motor Tesseract AI"]
    },
    "validador_links": {
        "name": "Validador de Links",
        "description": "Verifica se links estão ativos e produtos disponíveis",
        "icon": "link",
        "status": "coming_soon",
        "features": ["Varredura 24/7", "Alerta de Link Quebrado", "Check de Estoque"]
    },
    "extrator_reviews": {
        "name": "Extrator de Reviews",
        "description": "Extrai e analisa sentimento de reviews de marketplaces",
        "icon": "star",
        "status": "coming_soon",
        "features": ["Análise de Sentimento AI", "Exportação p/ CSV", "Gráfico de Notas"]
    },
    "calculadora_lucratividade": {
        "name": "Calculadora de Lucratividade",
        "description": "Calcula margem de lucro e identifica oportunidades de arbitragem",
        "icon": "calculator",
        "status": "coming_soon",
        "features": ["Simulador de Impostos", "Cálculo de ROI", "Break-even Point"]
    },
    "analista_tendencias": {
        "name": "Analista de Tendências",
        "description": "Identifica produtos trending em nichos específicos",
        "icon": "trending",
        "status": "coming_soon",
        "features": ["Google Trends Integration", "Top 100 Shopee", "Insights AI"]
    },
    "data_sanitizer": {
        "name": "Data Sanitizer",
        "description": "Limpa e normaliza dados de planilhas (CPF, CNPJ, nomes, endereços)",
        "icon": "cleaning",
        "status": "coming_soon",
        "features": ["Formatação CNPJ/CPF", "Limpeza de Nomes", "Normalização CEP"]
    },
    "gerador_laudos": {
        "name": "Gerador de Laudos",
        "description": "Gera laudos de conformidade cruzando extratos com notas fiscais",
        "icon": "document",
        "status": "coming_soon",
        "features": ["PDF assinado", "Conformidade Fiscal", "Logs de Auditoria"]
    },
    "comissoes": {
        "name": "Comissões",
        "description": "Calcule comissões de vendedores e gere relatórios individuais em PDF",
        "icon": "percent",
        "status": "coming_soon",
        "features": ["Regras Variáveis", "Relatório p/ WhatsApp", "Dashboard Vendedor"]
    }
}

# ==================== WEB SCRAPING (2024/2025) ====================
from src.utils.user_agents import UserAgentProvider
USER_AGENTS = UserAgentProvider.USER_AGENTS

def get_random_ua(device_type="desktop"):
    """Retorna um User-Agent aleatório (compatibilidade)"""
    return UserAgentProvider.get_random()

# ==================== CORES ====================
class Colors:
    DARK = {
        "BACKGROUND": "#09090B",
        "CARD": "#18181B",
        "CARD_TASK": "#27272A",
        "BORDER": "#27272A",
        "PRIMARY": "#d48214",
        "PRIMARY_HOVER": "#b5690f",
        "ALERT": "#EF4444",
        "TEXT_PRIMARY": "#FAFAFA",
        "TEXT_SECONDARY": "#A1A1AA"
    }
    
    LIGHT = {
        "BACKGROUND": "#FAFAFA",
        "CARD": "#FFFFFF",
        "CARD_TASK": "#18181B",
        "BORDER": "#E5E7EB",
        "PRIMARY": "#d48214",
        "PRIMARY_HOVER": "#b5690f",
        "ALERT": "#EF4444",
        "TEXT_PRIMARY": "#111827",
        "TEXT_SECONDARY": "#6B7280"
    }
    
    @staticmethod
    def update_from_theme(theme_name: str):
        theme = Colors.DARK if theme_name == "dark" else Colors.LIGHT if theme_name == "light" else Colors.DARK
        Colors.BACKGROUND = theme["BACKGROUND"]
        Colors.CARD = theme["CARD"]
        Colors.CARD_TASK = theme["CARD_TASK"]
        Colors.BORDER = theme["BORDER"]
        Colors.PRIMARY = theme["PRIMARY"]
        Colors.PRIMARY_HOVER = theme["PRIMARY_HOVER"]
        Colors.ALERT = theme["ALERT"]
        Colors.TEXT_PRIMARY = theme["TEXT_PRIMARY"]
        Colors.TEXT_SECONDARY = theme["TEXT_SECONDARY"]

# Inicialização padrão
Colors.update_from_theme("dark")

APP_URL_SITE = "https://data-master-pro.vercel.app/planos"
