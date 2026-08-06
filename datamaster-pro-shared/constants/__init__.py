"""
DataMaster Pro - Shared Constants and Types
"""

from enum import Enum
from typing import TypedDict, Optional, List

# ==================== PLANOS ====================
class PlanType(str, Enum):
    GRATIS = "gratis"
    STARTER = "starter"
    PRO = "pro"

class PlanInfo(TypedDict):
    id: str
    name: str
    max_lines_month: Optional[int]
    max_execs_month: Optional[int]
    tools: List[str]
    watermark: bool
    price: Optional[float]

PLANOS: dict[str, PlanInfo] = {
    "gratis": {
        "id": "gratis",
        "name": "Grátis",
        "max_lines_month": 1200,
        "max_execs_month": 15,
        "tools": ["consolidador", "categorizador", "orcamentos", "minerador", "conciliador", "conversor_ocr", "validador_links", "calculadora_lucratividade", "analista_tendencias", "comissoes", "classificador_ncm", "precificador_canal"],
        "watermark": True,
        "price": 0
    },
    "starter": {
        "id": "starter",
        "name": "Starter",
        "max_lines_month": 10000,
        "max_execs_month": 80,
        "tools": ["consolidador", "categorizador", "orcamentos", "minerador", "conciliador", "conversor_ocr", "validador_links", "calculadora_lucratividade", "analista_tendencias", "comissoes", "classificador_ncm", "precificador_canal"],
        "watermark": False,
        "price": 34.00
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "max_lines_month": None,
        "max_execs_month": None,
        "tools": ["all"],
        "watermark": False,
        "price": 64.00
    }
}

# ==================== FERRAMENTAS ====================
class ToolInfo(TypedDict):
    id: str
    name: str
    description: str
    icon: str
    min_plan: str

TOOLS: dict[str, ToolInfo] = {
    "consolidador": {
        "id": "consolidador",
        "name": "Consolidador",
        "description": "Une múltiplas planilhas em uma estrutura única",
        "icon": "merge",
        "min_plan": "gratis"
    },
    "categorizador": {
        "id": "categorizador",
        "name": "Categorizador",
        "description": "Classifica transações por palavras-chave",
        "icon": "tag",
        "min_plan": "gratis"
    },
    "orcamentos": {
        "id": "orcamentos",
        "name": "Orçamentos",
        "description": "Preenche templates de PDF em massa",
        "icon": "file",
        "min_plan": "gratis"
    },
    "minerador": {
        "id": "minerador",
        "name": "Minerador",
        "description": "Captura preços de sites concorrentes",
        "icon": "globe",
        "min_plan": "gratis"
    },
    "conciliador": {
        "id": "conciliador",
        "name": "Conciliador",
        "description": "Cruza extratos com planilhas de vendas",
        "icon": "check",
        "min_plan": "gratis"
    }
}

# ==================== CORES ====================
class Colors(TypedDict):
    background: str
    card: str
    border: str
    primary: str
    alert: str
    text_primary: str
    text_secondary: str

COLORS: Colors = {
    "background": "#0F172A",
    "card": "#1E293B",
    "border": "#334155",
    "primary": "#10B981",
    "alert": "#F59E0B",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8"
}

# ==================== STATUS ====================
class SyncStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SYNCED = "synced"
