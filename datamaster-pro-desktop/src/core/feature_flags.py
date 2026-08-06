"""
Feature Flags - Sistema de feature flags para rollout gradual
Permite habilitar/desabilitar funcionalidades por usuário, plano ou globalmente.

Flags podem vir de:
1. Config local (config.py) — para flags globais
2. Banco de dados (Supabase) — para flags por usuário/plan
3. Cache local (SQLite) — para operar offline
"""
import json
import threading
import logging
import time
from typing import Optional, Any
from pathlib import Path

log = logging.getLogger(__name__)


class FeatureFlag:
    """Definição de uma feature flag."""

    def __init__(
        self,
        key: str,
        default: bool = False,
        description: str = "",
        min_plan: str = None,
        rollout_percent: int = 100,
    ):
        self.key = key
        self.default = default
        self.description = description
        self.min_plan = min_plan
        self.rollout_percent = rollout_percent


# ── Flags conhecidas ─────────────────────────────────────────────────────────

KNOWN_FLAGS = {
    "realtime_sync": FeatureFlag(
        "realtime_sync",
        default=True,
        description="Sincronização em tempo real via WebSocket",
        rollout_percent=100,
    ),
    "dark_mode": FeatureFlag(
        "dark_mode",
        default=True,
        description="Modo escuro na interface",
    ),
    "export_premium": FeatureFlag(
        "export_premium",
        default=False,
        description="Exportação avançada com formatação profissional",
        min_plan="pro",
    ),
    "advanced_analytics": FeatureFlag(
        "advanced_analytics",
        default=False,
        description="Dashboard de analytics avançado",
        min_plan="pro",
    ),
    "auto_sync": FeatureFlag(
        "auto_sync",
        default=True,
        description="Sincronização automática ao reconectar",
    ),
    "browser_pool": FeatureFlag(
        "browser_pool",
        default=False,
        description="Pool de browsers compartilhado para mineração",
        rollout_percent=50,
    ),
    "circuit_breaker": FeatureFlag(
        "circuit_breaker",
        default=True,
        description="Circuit breaker para chamadas externas",
    ),
}


class FeatureFlagManager:
    """Gerencia feature flags com suporte a overrides por usuário/plan."""

    _instance: Optional["FeatureFlagManager"] = None

    def __init__(self):
        self._overrides: dict[str, dict] = {}
        self._remote_flags: dict[str, bool] = {}
        self._last_fetch: float = 0
        self._fetch_interval: float = 300  # 5 minutos
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "FeatureFlagManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_enabled(
        self,
        flag_key: str,
        user_data: dict = None,
        plan: str = None,
    ) -> bool:
        """Verifica se uma feature flag está habilitada.

        Prioridade:
        1. Override explícito (set_override)
        2. Flag remota do Supabase
        3. Rollout percentual
        4. Restrição de plano
        5. Default da flag
        """
        flag = KNOWN_FLAGS.get(flag_key)
        if flag is None:
            log.warning("Feature flag desconhecida: %s", flag_key)
            return False

        # 1. Override explícito
        with self._lock:
            if flag_key in self._overrides:
                return self._overrides[flag_key]

        # 2. Flag remota
        with self._lock:
            if flag_key in self._remote_flags:
                return self._remote_flags[flag_key]

        # 3. Rollout percentual (baseado no user_id para consistência)
        if flag.rollout_percent < 100:
            user_id = (user_data or {}).get("id", "anonymous")
            hash_val = hash(f"{flag_key}:{user_id}") % 100
            if hash_val >= flag.rollout_percent:
                return False

        # 4. Restrição de plano
        if flag.min_plan:
            effective_plan = plan or (user_data or {}).get("plan", "gratis")
            plan_order = {"gratis": 0, "starter": 1, "pro": 2}
            if plan_order.get(effective_plan, 0) < plan_order.get(flag.min_plan, 0):
                return False

        # 5. Default
        return flag.default

    def set_override(self, flag_key: str, enabled: bool):
        """Define override manual de uma flag."""
        with self._lock:
            self._overrides[flag_key] = enabled
        log.info("Feature flag override: %s = %s", flag_key, enabled)

    def clear_override(self, flag_key: str):
        """Remove override de uma flag."""
        with self._lock:
            self._overrides.pop(flag_key, None)

    def fetch_remote_flags(self, user_id: str = None):
        """Busca flags remotas do Supabase (async-friendly)."""
        now = time.time()
        if now - self._last_fetch < self._fetch_interval:
            return

        try:
            from src.core.services import get_user_service
            svc = get_user_service()
            token = svc.get_token()
            if not token:
                return

            from supabase import create_client
            import config
            client = create_client(config._u0, config._r1())
            client.postgrest.auth(token)

            result = client.table("feature_flags").select("*").execute()
            remote = {}
            for row in (result.data or []):
                key = row.get("flag_key")
                enabled = row.get("enabled", False)
                if key:
                    remote[key] = enabled

            with self._lock:
                self._remote_flags = remote
                self._last_fetch = now

            log.debug("Feature flags remotas carregadas: %d", len(remote))
        except Exception as e:
            log.warning("Erro ao buscar feature flags remotas: %s", e)

    def get_all_flags(self, user_data: dict = None) -> dict[str, dict]:
        """Retorna todas as flags com seu status atual."""
        result = {}
        for key, flag in KNOWN_FLAGS.items():
            result[key] = {
                "enabled": self.is_enabled(key, user_data),
                "description": flag.description,
                "min_plan": flag.min_plan,
                "rollout_percent": flag.rollout_percent,
            }
        return result


# ── Accessor global ──────────────────────────────────────────────────────────

def is_feature_enabled(flag_key: str, user_data: dict = None, plan: str = None) -> bool:
    """Atalho para verificar se uma feature flag está habilitada."""
    return FeatureFlagManager.get_instance().is_enabled(flag_key, user_data, plan)
