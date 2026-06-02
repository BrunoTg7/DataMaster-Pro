"""
FastAPI REST API — Desacopla desktop do Supabase
Permite que a web version acesse os mesmos dados via API própria.

Segurança:
- CORS restrito a origins configuradas
- JWT auth via Bearer token
- Rate limiting por IP
- Input validation via Pydantic
"""
import os
import sys
import time
import hashlib
import hmac
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime, timedelta
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, Depends, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

import config

log = logging.getLogger(__name__)

# ── Security ──────────────────────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)

# CORS — ONLY allow configured origins (no wildcard)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("API_CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
    if origin.strip()
]

# Rate limiting — per IP
_rate_limits: dict = {}
_rate_locks: dict = {}
RATE_LIMIT_REQUESTS = int(os.getenv("API_RATE_LIMIT", "60"))
RATE_LIMIT_WINDOW = 60  # seconds


def _get_rate_key(ip: str, endpoint: str) -> str:
    return f"{ip}:{endpoint}"


def check_rate_limit(ip: str, endpoint: str = "default") -> bool:
    """Retorna True se a requisição é permitida."""
    key = _get_rate_key(ip, endpoint)
    now = time.time()
    if key not in _rate_limits:
        _rate_limits[key] = []
    # Remove tokens expirados
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[key]) >= RATE_LIMIT_REQUESTS:
        return False
    _rate_limits[key].append(now)
    return True


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verifica JWT token e retorna user_data."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação necessário",
        )

    token = credentials.credentials
    try:
        from src.core.storage.user_storage import UserStorage
        storage = UserStorage()
        session = storage.get_saved_session()
        if session and session.get("session_token") == token:
            return session
    except Exception:
        pass

    # Fallback: verificar com Supabase
    try:
        from supabase import create_client
        client = create_client(config._u0, config._r1())
        client.postgrest.auth(token)
        user = client.auth.get_user()
        if user and user.user:
            return {"id": user.user.id, "email": user.user.email, "plan": "pro"}
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
    )


# ── Models ────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    email: str
    plan: str = "gratis"
    created_at: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    tool_name: str
    tool_display_name: str
    status: str
    progress_percent: int = 0
    progress_message: str = ""
    rows_processed: int = 0
    hours_saved: float = 0
    output_path: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None

class ExecutionResponse(BaseModel):
    id: Optional[int] = None
    tool_name: str
    rows_processed: int = 0
    hours_saved: float = 0
    created_at: str = ""

class StatsResponse(BaseModel):
    total_lines: int = 0
    total_hours: float = 0
    total_executions: int = 0
    by_tool: dict = {}

class SubmitTaskRequest(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=100)
    input_params: dict = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# ── App ───────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("DataMaster Pro API started (v%s)", config.APP_VERSION)
    yield
    log.info("DataMaster Pro API shutting down")

app = FastAPI(
    title="DataMaster Pro API",
    description="REST API para DataMaster Pro — Desktop & Web",
    version=config.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("API_DOCS_ENABLED", "false") == "true" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Rate Limit Middleware ─────────────────────────────────────────────────────

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path

    # Rate limit mais restritivo para auth endpoints
    limit = 10 if "/auth" in endpoint else RATE_LIMIT_REQUESTS

    key = _get_rate_key(client_ip, endpoint)
    now = time.time()
    if key not in _rate_limits:
        _rate_limits[key] = []
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[key]) >= limit:
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit excedido. Tente novamente em breve.",
        )
    _rate_limits[key].append(now)

    response = await call_next(request)
    return response


# ── Repositories (lazy init) ─────────────────────────────────────────────────

_repos = {}

def get_repos():
    if not _repos:
        from src.infrastructure.container import Container
        container = Container.get_instance()
        _repos["users"] = container.user_repo
        _repos["tasks"] = container.task_repo
        _repos["executions"] = container.execution_repo
        _repos["cache"] = container.cache
    return _repos


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check sem autenticação."""
    return HealthResponse(
        status="healthy",
        version=config.APP_VERSION,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/api/users/me", response_model=UserResponse)
def get_current_user(user: dict = Depends(verify_token)):
    """Retorna dados do usuário autenticado."""
    repos = get_repos()
    user_entity = repos["users"].get_user(user.get("id", ""))
    if not user_entity:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UserResponse(
        id=user_entity.id,
        email=user_entity.email,
        plan=user_entity.plan.value,
        created_at=user_entity.created_at,
    )


@app.get("/api/tasks", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[str] = Query(None, max_length=20),
    user: dict = Depends(verify_token),
):
    """Lista tarefas do usuário autenticado."""
    from src.core.tasks.task_executor import task_executor
    tasks = task_executor.get_tasks(status_filter=status)
    return [TaskResponse(**t) for t in tasks[:50]]


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, user: dict = Depends(verify_token)):
    """Retorna uma tarefa específica."""
    from src.core.tasks.task_executor import task_executor
    task = task_executor.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return TaskResponse(**task)


@app.post("/api/tasks/submit", response_model=TaskResponse)
def submit_task(req: SubmitTaskRequest, user: dict = Depends(verify_token)):
    """Submete uma nova tarefa."""
    from src.core.services import get_tool_service
    svc = get_tool_service()
    task_id, error = svc.create_task(
        req.tool_name,
        req.input_params,
        auto_execute=True,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    task = svc.get_task(task_id)
    return TaskResponse(**task)


@app.post("/api/tasks/{task_id}/cancel")
def cancel_task(task_id: str, user: dict = Depends(verify_token)):
    """Cancela uma tarefa."""
    from src.core.tasks.task_executor import task_executor
    result = task_executor.cancel_task(task_id)
    if not result:
        raise HTTPException(status_code=400, detail="Não foi possível cancelar")
    return {"status": "cancelled"}


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(user: dict = Depends(verify_token)):
    """Retorna estatísticas do usuário."""
    repos = get_repos()
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    cache = repos["cache"]
    cache_key = f"api_stats:{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return StatsResponse(**cached)

    from src.core.sync.sync_manager import ExecutionTracker, SyncManager
    from src.core.storage.storage_manager import StorageManager

    storage = StorageManager()
    sync = SyncManager(storage)
    tracker = ExecutionTracker(storage, sync)
    stats = tracker.get_user_stats(user_id)
    if stats:
        cache.set(cache_key, stats, ttl=30)
        return StatsResponse(**stats)
    return StatsResponse()


@app.get("/api/executions", response_model=List[ExecutionResponse])
def list_executions(
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(verify_token),
):
    """Lista execuções do usuário."""
    repos = get_repos()
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    execs = repos["executions"].get_executions(user_id, limit=limit)
    return [ExecutionResponse(**e) for e in execs]


@app.get("/api/tools")
def list_tools(user: dict = Depends(verify_token)):
    """Lista ferramentas disponíveis."""
    from src.tools.tool_registry import TOOL_REGISTRY, TOOL_PAGE_MODULES
    tools = []
    for key, cls in TOOL_REGISTRY.items():
        name = getattr(cls, "TOOL_NAME", key.replace("_", " ").title())
        tools.append({
            "key": key,
            "name": name,
            "page_module": TOOL_PAGE_MODULES.get(key, ""),
        })
    return tools


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
