"""
Plan Limits Manager - Verifica e valida limites de plano
Usa definições centralizadas de config.py para evitar contradições.
"""
from typing import Dict, Optional, Tuple
from enum import Enum
import logging
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

logger = logging.getLogger(__name__)


class PlanType(str, Enum):
    """Tipos de plano disponíveis - espelha config.PlanType"""
    GRATIS = "gratis"
    STARTER = "starter"
    PRO = "pro"


class PlanLimits:
    """Definição dos limites por plano - importa de config.py como fonte única"""
    
    @classmethod
    def get_limit(cls, plan: str, limit_key: str) -> any:
        """Obtém um limite específico para um plano"""
        try:
            plan_type = config.PlanType[plan.upper()] if plan.upper() in config.PlanType.__members__ else config.PlanType.GRATIS
            plan_data = config.PLAN_LIMITS.get(plan_type, {})
            return plan_data.get(limit_key)
        except (ValueError, KeyError):
            return config.PLAN_LIMITS.get(config.PlanType.GRATIS, {}).get(limit_key)

    @classmethod
    def get_all_limits(cls, plan: str) -> Dict:
        """Obtém todos os limites para um plano"""
        try:
            plan_type = config.PlanType[plan.upper()] if plan.upper() in config.PlanType.__members__ else config.PlanType.GRATIS
            return config.PLAN_LIMITS.get(plan_type, config.PLAN_LIMITS.get(config.PlanType.GRATIS, {})).copy()
        except (ValueError, KeyError):
            return config.PLAN_LIMITS.get(config.PlanType.GRATIS, {}).copy()


class PlanLimitValidator:
    """Valida se ações estão dentro dos limites do plano"""

    def __init__(self, user_plan: str, data_expiracao: str = None):
        self.user_plan = user_plan
        self.data_expiracao = data_expiracao
        self.limits = PlanLimits.get_all_limits(user_plan)

    def is_expired(self) -> bool:
        """
        Verifica se o plano (PRO/Enterprise) está com data de expiração vencida.
        Planos GRATIS nunca expiram.
        """
        if self.user_plan == config.PlanType.GRATIS.value:
            return False
        if not self.data_expiracao:
            return False
        try:
            exp_date = datetime.fromisoformat(self.data_expiracao.replace("Z", "+00:00").replace(" ", "T"))
            agora = datetime.now(exp_date.tzinfo) if exp_date.tzinfo else datetime.now()
            return exp_date <= agora
        except Exception:
            return False

    def _check_expired(self) -> Tuple[bool, Optional[str]]:
        """Retorna erro se o plano estiver expirado"""
        if self.is_expired():
            return False, (
                "Seu plano PRO expirou. "
                "Renove sua assinatura para continuar usando todos os recursos.\n\n"
                "Acesse: https://data-master-pro.vercel.app/planos"
            )
        return True, None

    def can_start_concurrent_task(self, current_running_tasks: int) -> Tuple[bool, Optional[str]]:
        """
        Verifica se pode iniciar outra tarefa concorrente
        
        Returns:
            (can_start, error_message)
        """
        ok, err = self._check_expired()
        if not ok:
            return False, err

        max_tasks = self.limits.get("max_concurrent_tasks", 1)
        
        if current_running_tasks >= max_tasks:
            message = (
                f"Limite de {max_tasks} tarefa(s) simultânea(s) atingido. "
                f"Aguarde a conclusão da(s) tarefa(s) anterior(es)."
            )
            if self.user_plan == config.PlanType.GRATIS.value:
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
        ok, err = self._check_expired()
        if not ok:
            return False, err

        max_size_mb = self.limits.get("max_file_size_mb", 5)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            message = (
                f"Arquivo muito grande ({file_size_mb:.1f}MB). "
                f"Máximo permitido: {max_size_mb}MB"
            )
            if self.user_plan == config.PlanType.GRATIS.value:
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
        ok, err = self._check_expired()
        if not ok:
            return False, err

        available_themes = self.limits.get("available_themes", ["classic_blue"])
        
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
        ok, err = self._check_expired()
        if not ok:
            return False, err

        supports = self.limits.get("supports_scheduling", False)
        
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
        ok, err = self._check_expired()
        if not ok:
            return False, err

        max_configs = self.limits.get("max_configs_per_tool", 3)
        
        if current_configs >= max_configs:
            message = (
                f"Limite de {max_configs} configuração(ões) atingido.\n"
                f"Delete uma configuração antiga ou upgrade para Pro."
            )
            return False, message
        
        return True, None

    def get_watermark_enabled(self) -> bool:
        """Retorna se marca d'água deve ser aplicada"""
        return self.limits.get("watermark", True)

    def get_roi_sync_mode(self) -> str:
        """Retorna modo de sincronização de logs ROI"""
        return self.limits.get("roi_logging", "local_only")

    def supports_background_execution(self) -> bool:
        """Verifica se plano suporta execução em background"""
        return self.limits.get("supports_background_execution", False)


# Singleton para uso global
_validator_instance: Optional[PlanLimitValidator] = None


def get_plan_validator(user_plan: str = None, data_expiracao: str = None) -> PlanLimitValidator:
    """Factory para obter instância do validador"""
    global _validator_instance
    
    if user_plan:
        _validator_instance = PlanLimitValidator(user_plan, data_expiracao)
    elif _validator_instance is None:
        _validator_instance = PlanLimitValidator(config.PlanType.GRATIS.value)
    
    return _validator_instance


def update_plan_validator(user_plan: str, data_expiracao: str = None) -> None:
    """Atualiza o validador com novo plano e data de expiração"""
    global _validator_instance
    _validator_instance = PlanLimitValidator(user_plan, data_expiracao)
