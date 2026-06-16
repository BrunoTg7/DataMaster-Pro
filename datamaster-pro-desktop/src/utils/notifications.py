"""
Desktop Notifications Module — Personalizado com winotify (Windows)
Fallback para plyer em outras plataformas.
"""
import os
import sys
import threading
import logging
from typing import Optional

log = logging.getLogger(__name__)

# ── Resolver caminho do ícone ────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    _BASE_PATH = sys._MEIPASS
else:
    _BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ICON_PATH = os.path.join(_BASE_PATH, "assets", "datamaster.ico")

# ── Tentar winotify (Windows) ────────────────────────────────────────────────
WINOTOIFY_AVAILABLE = False
try:
    from winotify import Notification, audio
    WINOTOIFY_AVAILABLE = True
except ImportError:
    pass

# ── Fallback: plyer (cross-platform) ─────────────────────────────────────────
PLYER_AVAILABLE = False
if not WINOTOIFY_AVAILABLE:
    try:
        from plyer import notification
        PLYER_AVAILABLE = True
    except ImportError:
        pass


class NotificationManager:
    """Gerenciador de notificações desktop personalizadas."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def _send_winotify(
        self,
        title: str,
        message: str,
        app_name: str = "DataMaster Pro",
        duration: int = 5,
        category: str = "info",
        sound: bool = True,
    ) -> bool:
        """Notificação Windows personalizada via winotify."""
        try:
            toast = Notification(
                app_id=app_name,
                title=title,
                msg=message,
                duration="short" if duration <= 5 else "long",
            )

            # Ícone customizado
            if os.path.exists(ICON_PATH):
                toast.set_audio(audio.Default, loop=False)
                toast.icon = ICON_PATH

            # Botão de ação: Abrir o app
            toast.add_actions(label="Abrir DataMaster Pro")

            toast.show()
            return True
        except Exception as e:
            log.warning("winotify falhou: %s", e)
            return False

    def _send_plyer(
        self,
        title: str,
        message: str,
        app_name: str = "DataMaster Pro",
        timeout: float = 5.0,
    ) -> bool:
        """Fallback cross-platform via plyer."""
        if not PLYER_AVAILABLE:
            return False
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=app_name,
                timeout=timeout,
            )
            return True
        except Exception:
            return False

    def send(
        self,
        title: str,
        message: str,
        app_name: str = "DataMaster Pro",
        timeout: float = 5.0,
        category: str = "info",
        sound: bool = True,
    ) -> bool:
        """
        Envia notificação desktop personalizada.

        Args:
            title: Título da notificação
            message: Corpo do texto
            app_name: Nome do app
            timeout: Duração em segundos
            category: 'info', 'success', 'warning', 'error'
            sound: Tocar som

        Returns:
            True se enviou com sucesso
        """
        if not self.enabled:
            return False

        # Adicionar emoji por categoria
        emoji_map = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️",
        }
        emoji = emoji_map.get(category, "")
        if emoji and not title.startswith(emoji):
            title = f"{emoji} {title}"

        if WINOTOIFY_AVAILABLE:
            return self._send_winotify(
                title=title,
                message=message,
                app_name=app_name,
                duration=int(timeout),
                category=category,
                sound=sound,
            )
        return self._send_plyer(
            title=title,
            message=message,
            app_name=app_name,
            timeout=timeout,
        )

    def send_async(
        self,
        title: str,
        message: str,
        app_name: str = "DataMaster Pro",
        timeout: float = 5.0,
        category: str = "info",
        sound: bool = True,
    ) -> None:
        """Envia notificação em thread separada (não bloqueia a UI)."""
        thread = threading.Thread(
            target=self.send,
            args=(title, message),
            kwargs={"app_name": app_name, "timeout": timeout, "category": category, "sound": sound},
            daemon=True,
        )
        thread.start()

    def task_completed(
        self,
        tool_name: str,
        records_count: int = 0,
        hours_saved: float = 0,
    ) -> bool:
        """Notificação de tarefa concluída."""
        if records_count > 0:
            message = f"{tool_name} finalizada com {records_count} registros processados."
        else:
            message = f"{tool_name} finalizada com sucesso."

        if hours_saved > 0:
            message += f"\nTempo economizado: {hours_saved:.1f}h."

        return self.send(
            title=f"{tool_name} Concluído!",
            message=message,
            category="success",
        )

    def task_completed_async(
        self,
        tool_name: str,
        records_count: int = 0,
        hours_saved: float = 0,
    ) -> None:
        """Notificação de tarefa concluída em background."""
        self.send_async(
            title=f"{tool_name} Concluído!",
            message=f"{tool_name} finalizada com {records_count} registros.",
            category="success",
        )

    def error(self, title: str, message: str) -> bool:
        """Notificação de erro."""
        return self.send(title=title, message=message, category="error")

    def error_async(self, title: str, message: str) -> None:
        """Notificação de erro em background."""
        self.send_async(title=title, message=message, category="error")

    def warning(self, title: str, message: str) -> bool:
        """Notificação de aviso."""
        return self.send(title=title, message=message, category="warning")

    def warning_async(self, title: str, message: str) -> None:
        """Notificação de aviso em background."""
        self.send_async(title=title, message=message, category="warning")


# ── Singleton ────────────────────────────────────────────────────────────────
notification_manager = NotificationManager()


def send_notification(
    title: str,
    message: str,
    enabled: bool = True,
    category: str = "info",
) -> bool:
    """Função conveniente para enviar notificações."""
    if not enabled:
        return False
    return notification_manager.send(title, message, category=category)


def notify_task_complete(
    tool_name: str,
    records_count: int = 0,
    enabled: bool = True,
) -> bool:
    """Função conveniente para notificar conclusão de tarefa."""
    if not enabled:
        return False
    return notification_manager.task_completed(tool_name, records_count)
