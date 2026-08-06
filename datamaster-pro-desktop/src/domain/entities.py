"""
Domain Entities - Entidades de negócio puras
Zero dependências externas. Apenas dataclasses e enums.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class PlanType(Enum):
    GRATIS = "gratis"
    STARTER = "starter"
    PRO = "pro"


class SyncStatus(Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass
class User:
    id: str
    email: str = ""
    plan: PlanType = PlanType.GRATIS
    hwid: str = ""
    data_expiracao: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def is_pro(self) -> bool:
        return self.plan == PlanType.PRO


@dataclass
class Task:
    id: str
    tool_name: str
    tool_display_name: str
    user_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    progress_percent: int = 0
    progress_message: str = "Aguardando..."
    error_message: str = ""
    rows_processed: int = 0
    hours_saved: float = 0
    output_path: str = ""
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None
    input_params: str = "{}"
    log_messages: List[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return self.status in (TaskStatus.PENDING, TaskStatus.RUNNING)

    @property
    def is_done(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)


@dataclass
class Execution:
    id: Optional[int] = None
    user_id: str = ""
    tool_name: str = ""
    input_files: str = "[]"
    output_path: str = ""
    rows_processed: int = 0
    hours_saved: float = 0
    status: str = "completed"
    duration_ms: int = 0
    created_at: str = ""


@dataclass
class ToolMetadata:
    """Metadados de uma ferramenta (para plugin system)."""
    key: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    page_module: str = ""
    min_plan: PlanType = PlanType.GRATIS
    enabled: bool = True


@dataclass
class SyncQueueItem:
    id: Optional[int] = None
    operation: str = ""
    table_name: str = ""
    data_json: str = "{}"
    usuario_id: str = ""
    status: SyncStatus = SyncStatus.PENDING
    retry_count: int = 0
    created_at: str = ""
    synced_at: Optional[str] = None


@dataclass
class FeatureFlagEntity:
    key: str
    enabled: bool = False
    description: str = ""
    min_plan: Optional[str] = None
    rollout_percent: int = 100
