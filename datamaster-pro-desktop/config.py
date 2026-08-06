# DataMaster Pro - Global Configuration

import os
import logging
from enum import Enum
import sys
from dotenv import load_dotenv

# Configurar logging básico para config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Carrega .env se existir
load_dotenv()

# ==================== AMBIENTE ====================
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# ==================== APP ====================
APP_NAME = os.getenv("APP_NAME", "DataMaster Pro")
APP_VERSION = os.getenv("APP_VERSION", "1.2.8")
THEME = os.getenv("THEME", "dark")
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SYNC_INTERVAL_MS = 30000

# ==================== DIRETÓRIOS ====================
if getattr(sys, 'frozen', False):
    # COMPILADO: Usar AppData para TUDO (sem permissões de admin)
    BASE_DIR = os.path.dirname(sys.executable)
    USER_DATA = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'DataMaster Pro')
    LOGS_DIR = os.path.join(USER_DATA, "logs")
    CACHE_DIR = os.path.join(USER_DATA, "cache")
    DB_PATH = os.path.join(USER_DATA, "datamaster.db")
    OUTPUT_DIR = os.path.join(USER_DATA, "outputs")
else:
    # DESENVOLVIMENTO: Usar pastas locais
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    USER_DATA = BASE_DIR
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    DB_PATH = os.path.join(BASE_DIR, "datamaster.db")
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
APP_DATA_DIR = USER_DATA

# Garanta que diretórios existam (simples, sem fallback complexo)
for d in [LOGS_DIR, CACHE_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

# ==================== MIGRAÇÃO DE DADOS ANTIGOS ====================
# IMPORTANTE: Executar ANTES de qualquer outra inicialização
def _migrate_old_database():
    """Copia dados do banco antigo (Program Files) para o novo (AppData)"""
    if getattr(sys, 'frozen', False):
        old_data_dir = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'DataMaster Pro')
        old_db_path = os.path.join(old_data_dir, 'datamaster.db')
        
        if os.path.exists(old_db_path):
            try:
                import shutil
                
                if not os.path.exists(DB_PATH):
                    shutil.copy2(old_db_path, DB_PATH)
                    log.info("Banco de dados migrado: %s", DB_PATH)
                else:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
                        tmp_path = tmp.name
                    
                    shutil.copy2(old_db_path, tmp_path)
                    
                    log.info("Sincronizando com banco antigo...")
                    import sqlite3
                    new_conn = sqlite3.connect(DB_PATH)
                    new_cursor = new_conn.cursor()
                    new_cursor.execute("SELECT COUNT(*) FROM users WHERE session_token_encrypted IS NOT NULL")
                    has_session = new_cursor.fetchone()[0] > 0
                    new_conn.close()
                    
                    if not has_session:
                        shutil.copy2(old_db_path, DB_PATH)
                        log.info("Sessão restaurada do banco antigo")
                
                old_outputs = os.path.join(old_data_dir, 'outputs')
                if os.path.exists(old_outputs) and os.path.isdir(old_outputs):
                    for file in os.listdir(old_outputs):
                        src = os.path.join(old_outputs, file)
                        dst = os.path.join(OUTPUT_DIR, file)
                        if os.path.isfile(src):
                            try:
                                if not os.path.exists(dst):
                                    shutil.copy2(src, dst)
                            except OSError as e:
                                log.warning("Erro ao copiar output %s: %s", file, e)
                    log.info("Outputs sincronizados")
                
                old_logs = os.path.join(old_data_dir, 'logs')
                if os.path.exists(old_logs) and os.path.isdir(old_logs):
                    for file in os.listdir(old_logs):
                        src = os.path.join(old_logs, file)
                        dst = os.path.join(LOGS_DIR, file)
                        if os.path.isfile(src):
                            try:
                                if not os.path.exists(dst):
                                    shutil.copy2(src, dst)
                            except OSError as e:
                                log.warning("Erro ao copiar log %s: %s", file, e)
                    log.info("Logs sincronizados")
                    
            except Exception as e:
                log.error("Erro na migração de banco antigo: %s", e)

# Executar migração IMEDIATAMENTE, antes de qualquer outra coisa
_migrate_old_database()

# ==================== REDE INTERNA ====================
_r0 = None

def _r1() -> str:
    global _r0
    if _r0 is not None:
        return _r0
    try:
        from src.utils._net._z import _f
        _r0 = _f()
    except Exception:
        _r0 = os.getenv("SUPABASE_ANON_KEY", "")
    return _r0

_g0 = None

def _g1() -> str:
    global _g0
    if _g0 is not None:
        return _g0
    try:
        from src.utils._net._z import _g
        _g0 = _g()
    except Exception:
        _g0 = ""
    return _g0

# ==================== REDE ====================
_u0 = os.getenv("SUPABASE_URL", "")

# ==================== CRIPTOGRAFIA ====================
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# ==================== ESTADO DE SESSÃO ====================
SESSION_UPDATE_CHECKED = False
LAST_UPDATE_DATA = None
SESSION_BANNER_SHOWN = False

# Validação
if not _u0:
    raise ValueError(
        "Erro de configuração. Verifique se o arquivo .env existe e está configurado corretamente."
    )

_supabase_key = _r1()
if not _supabase_key:
    log.warning("SUPABASE_KEY não configurada. Verifique src/utils/_net/_z.py ou a variável de ambiente.")

# ==================== PLANOS E LIMITES ====================
class PlanType(Enum):
    GRATIS = "gratis"
    STARTER = "starter"
    PRO = "pro"

PLAN_LIMITS = {
    PlanType.GRATIS: {
        "max_lines_month": 1200,
        "max_execs_month": 15,
        "max_concurrent_tasks": 1,
        "available_history_retentions": ["1h"],
        "tools": ["consolidador", "categorizador", "orcamentos", "minerador", "conciliador", "conversor_ocr", "validador_links", "calculadora_lucratividade", "analista_tendencias", "comissoes", "classificador_ncm", "precificador_canal"],
        "tools_limit": {
            "consolidador": {"max_per_exec": 600, "max_execs": 5},
            "categorizador": {"max_per_exec": 600, "max_execs": 5},
            "orcamentos": {"max_per_exec": 15, "max_execs": 3},
            "minerador": {"max_per_exec": 15, "max_total": 15, "max_execs": 2},
            "conciliador": {"max_execs": 2},
            "conversor_ocr": {"max_per_exec": 10, "max_execs": 3},
            "validador_links": {"max_per_exec": 20, "max_execs": 3},
            "calculadora_lucratividade": {"max_execs": 3},
            "analista_tendencias": {"max_per_exec": 5, "max_execs": 3},
            "comissoes": {"max_per_exec": 20, "max_execs": 3},
            "classificador_ncm": {"max_per_exec": 100, "max_execs": 3},
            "precificador_canal": {"max_per_exec": 100, "max_execs": 3},
        }
    },
    PlanType.STARTER: {
        "max_lines_month": 10000,
        "max_execs_month": 80,
        "max_concurrent_tasks": 2,
        "available_history_retentions": ["7d", "15d", "1m", "6m"],
        "tools": ["consolidador", "categorizador", "orcamentos", "minerador", "conciliador", "conversor_ocr", "validador_links", "calculadora_lucratividade", "analista_tendencias", "comissoes", "classificador_ncm", "precificador_canal"],
        "tools_limit": {
            "consolidador": {"max_per_exec": 3000, "max_execs": 10},
            "categorizador": {"max_per_exec": 3000, "max_execs": 10},
            "orcamentos": {"max_per_exec": 60, "max_execs": 6},
            "minerador": {"max_per_exec": 80, "max_total": 80, "max_execs": 8},
            "conciliador": {"max_execs": 8},
            "conversor_ocr": {"max_per_exec": 20, "max_execs": 6},
            "validador_links": {"max_per_exec": 40, "max_execs": 6},
            "calculadora_lucratividade": {"max_execs": 6},
            "analista_tendencias": {"max_per_exec": 10, "max_execs": 6},
            "comissoes": {"max_per_exec": 40, "max_execs": 6},
            "classificador_ncm": {"max_per_exec": 200, "max_execs": 6},
            "precificador_canal": {"max_per_exec": 200, "max_execs": 6},
        }
    },
    PlanType.PRO: {
        "max_lines_month": 999999,
        "max_execs_month": 999,
        "max_concurrent_tasks": 2,
        "available_history_retentions": ["7d", "15d", "1m", "6m"],
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
    },
    "classificador_ncm": {
        "name": "Classificador NCM",
        "description": "Classifica produtos com códigos NCM e CEST corretos via fuzzy matching",
        "icon": "tag",
        "status": "coming_soon",
        "features": ["Fuzzy Matching NCM/CEST", "Planilha em Massa", "Sugestão Automática"]
    },
    "precificador_canal": {
        "name": "Precificador de Canal",
        "description": "Calcula preços por marketplace (ML, Shopee, Amazon, Magalu) garantindo margem líquida",
        "icon": "calculator",
        "status": "coming_soon",
        "features": ["Simulador Impostos", "Cálculo Reverso", "Margem Líquida"]
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
