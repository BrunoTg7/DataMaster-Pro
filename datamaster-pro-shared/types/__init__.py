"""
TypeScript Types para DataMaster Pro - Shared
"""

# User Types
from typing import Literal, Optional
from datetime import datetime

class User:
    id: str
    email: str
    nome: str
    plano_tipo: Literal["gratis", "starter", "pro"]
    data_expiracao: datetime
    created_at: datetime
    updated_at: datetime

# Execution Types
class Execution:
    id: str
    usuario_id: str
    ferramenta: str
    linhas_processadas: int
    tempo_execucao_ms: int
    tempo_economizado_minutos: int
    resultado_arquivo: str
    status: str  # pending, synced, failed
    created_at: datetime

# Plan Types
class Plan:
    id: str
    name: str
    max_lines: Optional[int]
    tools: list[str]
    watermark: bool
    price: Optional[float]

# Tool Types
class Tool:
    id: str
    name: str
    description: str
    icon: str
    min_plan: str

# Sync Types
class SyncQueue:
    id: str
    execution_id: str
    status: str  # pending, syncing, synced
    error_message: Optional[str]
    created_at: datetime
    synced_at: Optional[datetime]
