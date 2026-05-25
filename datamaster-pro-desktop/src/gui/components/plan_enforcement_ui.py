"""
Plan Enforcement UI - Components para exibir restrições de plano
"""
import customtkinter as ctk
from tkinter import messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class PlanRestrictedModal(ctk.CTkToplevel):
    """
    Modal para informar que recurso está disponível apenas em plano superior
    """
    
    def __init__(self, parent, title: str, message: str, feature: str = "", plan_required: str = "Pro"):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("500x300")
        self.resizable(False, False)
        
        # Centro na tela
        self.transient(parent)
        self.grab_set()
        
        # ===== HEADER =====
        header_frame = ctk.CTkFrame(self, fg_color=config.Colors.PRIMARY, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text="🔒",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=15)
        
        # ===== CONTENT =====
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            justify="left",
            wraplength=450
        )
        message_label.pack(pady=(0, 15))
        
        if feature:
            feature_label = ctk.CTkLabel(
                content_frame,
                text=f"Recurso: {feature}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=config.Colors.PRIMARY
            )
            feature_label.pack(pady=(0, 5))
        
        plan_label = ctk.CTkLabel(
            content_frame,
            text=f"Disponível a partir do plano: {plan_required}",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        plan_label.pack(pady=(0, 15))
        
        # ===== BUTTONS =====
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        upgrade_btn = ctk.CTkButton(
            button_frame,
            text="✨ Fazer Upgrade",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=config.Colors.PRIMARY,
            hover_color="#08A46A",
            command=self._on_upgrade
        )
        upgrade_btn.pack(side="left", padx=(0, 10))
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_PRIMARY,
            hover_color=config.Colors.CARD,
            command=self.destroy
        )
        close_btn.pack(side="left")
    
    def _on_upgrade(self):
        """Callback para upgrade (pode ser sobrescrito)"""
        messagebox.showinfo(
            "Upgrade",
            "Redirecionando para página de planos...\n(Funcionalidade a ser implementada)"
        )
        self.destroy()


class ConcurrentTasksLimitModal(ctk.CTkToplevel):
    """
    Modal para informar limite de tarefas simultâneas atingido
    """
    
    def __init__(self, parent, current_tasks: int, max_tasks: int, user_plan: str = "gratis"):
        super().__init__(parent)
        
        self.title("Limite de Tarefas Atingido")
        self.geometry("480x280")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        # ===== HEADER =====
        header_frame = ctk.CTkFrame(self, fg_color="#F59E0B", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text="⏳",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=15)
        
        # ===== CONTENT =====
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content_frame,
            text="Limite de Tarefas Simultâneas Atingido",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 10))
        
        info_text = f"Você tem {current_tasks} tarefa(s) em execução.\nMáximo permitido: {max_tasks} tarefa(s)."
        info_label = ctk.CTkLabel(
            content_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            justify="left"
        )
        info_label.pack(pady=(0, 15))
        
        if user_plan == "gratis":
            upgrade_text = ctk.CTkLabel(
                content_frame,
                text="💡 Dica: Upgrade para PRO para executar 2 tarefas simultâneas!",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=config.Colors.PRIMARY
            )
            upgrade_text.pack(pady=(0, 15))
        
        wait_text = ctk.CTkLabel(
            content_frame,
            text="Aguarde a conclusão da(s) tarefa(s) atual(is) antes de iniciar uma nova.",
            font=ctk.CTkFont(size=10),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=440
        )
        wait_text.pack(pady=(0, 15))
        
        # ===== BUTTONS =====
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        if user_plan == "gratis":
            upgrade_btn = ctk.CTkButton(
                button_frame,
                text="✨ Upgrade para PRO",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=config.Colors.PRIMARY,
                hover_color="#08A46A",
                command=self._on_upgrade
            )
            upgrade_btn.pack(side="left", padx=(0, 10))
        
        ok_btn = ctk.CTkButton(
            button_frame,
            text="OK",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_PRIMARY,
            hover_color=config.Colors.CARD,
            command=self.destroy
        )
        ok_btn.pack(side="left")
    
    def _on_upgrade(self):
        """Callback para upgrade"""
        messagebox.showinfo(
            "Upgrade",
            "Redirecionando para página de planos...\n(Funcionalidade a ser implementada)"
        )
        self.destroy()


class FileSizeLimitModal(ctk.CTkToplevel):
    """
    Modal para informar limite de tamanho de arquivo atingido
    """
    
    def __init__(self, parent, file_size_mb: float, max_size_mb: int, user_plan: str = "gratis"):
        super().__init__(parent)
        
        self.title("Arquivo Muito Grande")
        self.geometry("480x300")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        # ===== HEADER =====
        header_frame = ctk.CTkFrame(self, fg_color="#EF4444", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text="📁",
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=15)
        
        # ===== CONTENT =====
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            content_frame,
            text="Arquivo Muito Grande",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 10))
        
        info_text = f"Arquivo: {file_size_mb:.1f}MB\nLimite: {max_size_mb}MB"
        info_label = ctk.CTkLabel(
            content_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            justify="left"
        )
        info_label.pack(pady=(0, 15))
        
        if user_plan == "gratis":
            upgrade_text = ctk.CTkLabel(
                content_frame,
                text=f"💡 Upgrade para PRO para processar arquivos até 100MB!",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=config.Colors.PRIMARY
            )
            upgrade_text.pack(pady=(0, 15))
        
        suggestion_text = ctk.CTkLabel(
            content_frame,
            text="Solução: Divida o arquivo em partes menores ou comprima-o antes de enviar.",
            font=ctk.CTkFont(size=10),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=440
        )
        suggestion_text.pack(pady=(0, 15))
        
        # ===== BUTTONS =====
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        if user_plan == "gratis":
            upgrade_btn = ctk.CTkButton(
                button_frame,
                text="✨ Upgrade para PRO",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=config.Colors.PRIMARY,
                hover_color="#08A46A",
                command=self._on_upgrade
            )
            upgrade_btn.pack(side="left", padx=(0, 10))
        
        ok_btn = ctk.CTkButton(
            button_frame,
            text="OK",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_PRIMARY,
            hover_color=config.Colors.CARD,
            command=self.destroy
        )
        ok_btn.pack(side="left")
    
    def _on_upgrade(self):
        """Callback para upgrade"""
        messagebox.showinfo(
            "Upgrade",
            "Redirecionando para página de planos...\n(Funcionalidade a ser implementada)"
        )
        self.destroy()


def show_plan_restricted(parent, feature: str, required_plan: str = "Pro"):
    """Função helper para mostrar modal de restrição"""
    modal = PlanRestrictedModal(
        parent,
        title=f"{feature} - Plano Restrito",
        message=f"O recurso '{feature}' está disponível apenas no plano {required_plan}.",
        feature=feature,
        plan_required=required_plan
    )


def show_concurrent_limit(parent, current_tasks: int, max_tasks: int, user_plan: str = "gratis"):
    """Função helper para mostrar modal de limite de tarefas"""
    modal = ConcurrentTasksLimitModal(parent, current_tasks, max_tasks, user_plan)


def show_file_size_limit(parent, file_size_mb: float, max_size_mb: int, user_plan: str = "gratis"):
    """Função helper para mostrar modal de limite de arquivo"""
    modal = FileSizeLimitModal(parent, file_size_mb, max_size_mb, user_plan)
