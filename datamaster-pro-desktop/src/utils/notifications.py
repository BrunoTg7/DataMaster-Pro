"""
Cross-platform Desktop Notifications Module
Supports Windows, macOS, and Linux
"""

import threading
import platform
from typing import Optional

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class NotificationManager:
    """Cross-platform notification manager"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._system = platform.system()
    
    def send(
        self,
        title: str,
        message: str,
        app_name: str = "DataMaster Pro",
        timeout: float = 5.0
    ) -> bool:
        """
        Send a desktop notification
        
        Args:
            title: Notification title
            message: Notification body text
            app_name: Application name displayed in notification
            timeout: How long to show the notification (seconds)
            
        Returns:
            True if notification was sent successfully
        """
        if not self.enabled:
            return False
        
        if not PLYER_AVAILABLE:
            return False
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=app_name,
                timeout=timeout
            )
            return True
        except Exception:
            return False
    
    def send_async(
        self,
        title: str,
        message: str,
        app_name: str = "DataMaster Pro",
        timeout: float = 5.0
    ) -> None:
        """Send notification in background thread"""
        thread = threading.Thread(
            target=self.send,
            args=(title, message, app_name, timeout),
            daemon=True
        )
        thread.start()
    
    def task_completed(
        self,
        tool_name: str,
        records_count: int = 0
    ) -> bool:
        """Send notification when a tool finishes processing"""
        if records_count > 0:
            message = f"{tool_name} finalizada com {records_count} registros processados."
        else:
            message = f"{tool_name} finalizada com sucesso."
        
        return self.send(
            title="Tarefa Concluída",
            message=message
        )
    
    def task_completed_async(
        self,
        tool_name: str,
        records_count: int = 0
    ) -> None:
        """Send task completed notification in background"""
        self.send_async(
            title="Tarefa Concluída",
            message=f"{tool_name} finalizada com {records_count} registros."
        )


notification_manager = NotificationManager()


def send_notification(
    title: str,
    message: str,
    enabled: bool = True
) -> bool:
    """Convenience function to send notifications"""
    if not enabled:
        return False
    return notification_manager.send(title, message)


def notify_task_complete(
    tool_name: str,
    records_count: int = 0,
    enabled: bool = True
) -> bool:
    """Convenience function to notify task completion"""
    if not enabled:
        return False
    return notification_manager.task_completed(tool_name, records_count)