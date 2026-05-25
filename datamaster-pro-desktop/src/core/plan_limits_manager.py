"""
Plan Limits Manager - Verifica e valida limites de plano
"""
from typing import Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlanType(str, Enum):
    """Tipos de plano disponíveis"""
    GRATIS = "gratis"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PlanLimits:
    """Definição dos limites por plano"""
    
    LIMITS = {
        PlanType.GRATIS: {
            "max_concurrent_tasks": 1,
            "max_file_size_mb": 5,
            "max_configs_per_tool": 3,
            "supports_scheduling": False,
            "supports_background_execution": False,
            "watermark": True,
            "available_themes": ["classic_blue"],
            "roi_logging": "local_only",
            "max_daily_executions": 15,
        },
        PlanType.PRO: {
            "max_concurrent_tasks": 2,
            "max_file_size_mb": 100,
            "max_configs_per_tool": 20,
            "supports_scheduling": True,
            "supports_background_execution": False,
            "watermark": False,
            "available_themes": ["classic_blue", "emerald_green", "modern_orange", "slate_gray"],
            "roi_logging": "local_and_cloud",
            "max_daily_executions": None,  # Ilimitado
        },
        PlanType.ENTERPRISE: {
            "max_concurrent_tasks": 2,
            "max_file_size_mb": 100,
            "max_configs_per_tool": 999,  # Praticamente ilimitado
            "supports_scheduling": True,
            "supports_background_execution": True,
            "watermark": False,
            "available_themes": ["classic_blue", "emerald_green", "modern_orange", "slate_gray"],
            "roi_logging": "local_and_cloud",
            "max_daily_executions": None,
        },
    }

    @classmethod
    def get_limit(cls, plan: str, limit_key: str) -> any:
        """Obtém um limite específico para um plano"""
        try:
            plan_type = PlanType(plan)
            return cls.LIMITS[plan_type].get(limit_key)
        except (ValueError, KeyError):
            # Se plano inválido, retornar limites mais restritivos (FREE)
            return cls.LIMITS[PlanType.GRATIS].get(limit_key)

    @classmethod
    def get_all_limits(cls, plan: str) -> Dict:
        """Obtém todos os limites para um plano"""
        try:
            plan_type = PlanType(plan)
            return cls.LIMITS[plan_type].copy()
        except ValueError:
            return cls.LIMITS[PlanType.GRATIS].copy()


class PlanLimitValidator:
    """Valida se ações estão dentro dos limites do plano"""

    def __init__(self, user_plan: str):
        self.user_plan = user_plan
        self.limits = PlanLimits.get_all_limits(user_plan)

    def can_start_concurrent_task(self, current_running_tasks: int) -> Tuple[bool, Optional[str]]:
        """
        Verifica se pode iniciar outra tarefa concorrente
        
        Returns:
            (can_start, error_message)
        """
        max_tasks = self.limits["max_concurrent_tasks"]
        
        if current_running_tasks >= max_tasks:
            message = (
                f"Limite de {max_tasks} tarefa(s) simultânea(s) atingido. "
                f"Aguarde a conclusão da(s) tarefa(s) anterior(es)."
            )
            if self.user_plan == PlanType.GRATIS:
                message += "\n\nUpgrade para PRO para executar 2 tarefas simultâneas."
            return False, message
        
        return True, None

    def validate_file_size(self, file_size_bytes: int) -> Tuple[bool, Optional[str]]:
        """
        Verifica se o arquivo está dentro do limite
        
        Args:
            file_size_bytes: Tamanho do arquivo em bytes
            
        Returns:
            (is_valid, error_message)
        """
        max_size_mb = self.limits["max_file_size_mb"]
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            message = (
                f"Arquivo muito grande ({file_size_mb:.1f}MB). "
                f"Máximo permitido: {max_size_mb}MB"
            )
            if self.user_plan == PlanType.GRATIS:
                message += "\n\nUpgrade para PRO para processar arquivos até 100MB."
            return False, message
        
        return True, None

    def validate_theme_access(self, theme_key: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica se o usuário tem acesso ao tema
        
        Args:
            theme_key: ID do tema (ex: 'classic_blue')
            
        Returns:
            (has_access, error_message)
        """
        available_themes = self.limits["available_themes"]
        
        if theme_key not in available_themes:
            message = (
                f"O tema '{theme_key}' está disponível apenas no plano Pro.\n"
                f"Temas disponíveis: {', '.join(available_themes)}"
            )
            return False, message
        
        return True, None

    def validate_scheduling(self) -> Tuple[bool, Optional[str]]:
        """
        Verifica se o plano suporta agendamento
        
        Returns:
            (supports_scheduling, error_message)
        """
        supports = self.limits["supports_scheduling"]
        
        if not supports:
            message = (
                "Agendamento de tarefas está disponível apenas no plano Pro.\n"
                "Crie tarefas manuais ou upgrade para Pro."
            )
            return False, message
        
        return True, None

    def validate_config_storage(self, current_configs: int) -> Tuple[bool, Optional[str]]:
        """
        Verifica se pode adicionar mais uma configuração
        
        Args:
            current_configs: Número de configurações atuais
            
        Returns:
            (can_add, error_message)
        """
        max_configs = self.limits["max_configs_per_tool"]
        
        if current_configs >= max_configs:
            message = (
                f"Limite de {max_configs} configuração(ões) atingido.\n"
                f"Delete uma configuração antiga ou upgrade para Pro."
            )
            return False, message
        
        return True, None

    def get_watermark_enabled(self) -> bool:
        """Retorna se marca d'água deve ser aplicada"""
        return self.limits["watermark"]

    def get_roi_sync_mode(self) -> str:
        """Retorna modo de sincronização de logs ROI"""
        return self.limits["roi_logging"]

    def supports_background_execution(self) -> bool:
        """Verifica se plano suporta execução em background"""
        return self.limits["supports_background_execution"]


# Singleton para uso global
_validator_instance: Optional[PlanLimitValidator] = None


def get_plan_validator(user_plan: str = None) -> PlanLimitValidator:
    """Factory para obter instância do validador"""
    global _validator_instance
    
    if user_plan:
        _validator_instance = PlanLimitValidator(user_plan)
    elif _validator_instance is None:
        # Default to FREE se nenhum plano especificado
        _validator_instance = PlanLimitValidator(PlanType.GRATIS)
    
    return _validator_instance


def update_plan_validator(user_plan: str) -> None:
    """Atualiza o validador com novo plano"""
    global _validator_instance
    _validator_instance = PlanLimitValidator(user_plan)
