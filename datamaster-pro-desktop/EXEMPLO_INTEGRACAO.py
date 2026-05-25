"""
Exemplo de Integração - Demonstração do Sistema de Execução Paralela

Este arquivo mostra como integrar ferramentas com o novo ExecutionManager
"""
import sys
import os
import time
import threading
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import customtkinter as ctk
import config
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.execution_manager import get_execution_manager


class ExemploFerramentaPage(ctk.CTkFrame):
    """Exemplo de ferramenta com suporte a execução paralela"""
    
    def __init__(self, master, tool_name: str, user_id: str = None):
        super().__init__(master, fg_color=config.Colors.BACKGROUND)
        
        self.tool_name = tool_name
        self.user_id = user_id
        
        # Criar helper de execução
        self.execution = ExecutionHelper(
            tool_key=tool_name.lower().replace(" ", "_"),
            tool_display_name=tool_name,
            user_id=user_id or "demo_user"
        )
        
        self._create_ui()
    
    def _create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, fg_color=config.Colors.CARD, height=60)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header,
            text=f"Exemplo: {self.tool_name}",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.PRIMARY
        )
        title.pack(pady=15, padx=20)
        
        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)
        
        # Descrição
        desc = ctk.CTkLabel(
            content,
            text="Demonstração de Execução Paralela com Persistência",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        desc.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        # Botão de execução
        exec_btn = ctk.CTkButton(
            content,
            text="▶ Iniciar Processamento",
            height=40,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            command=self._start_processing
        )
        exec_btn.grid(row=1, column=0, sticky="ew", pady=10)
        
        # Status local
        self.status_label = ctk.CTkLabel(
            content,
            text="Aguardando...",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.grid(row=2, column=0, sticky="ew", pady=10)
        
        # Barra de progresso local
        self.progress_bar = ctk.CTkProgressBar(content, height=8)
        self.progress_bar.grid(row=3, column=0, sticky="ew", pady=10)
        self.progress_bar.set(0)
        
        # Log area
        log_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        log_frame.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="Log de Execução:",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        log_title.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Courier", size=10))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.log_text.configure(state="disabled")
        
        content.grid_rowconfigure(4, weight=1)
    
    def _start_processing(self):
        """Inicia processamento de exemplo"""
        # Criar tarefa
        task_id, error = self.execution.create_task(
            on_progress=self._on_progress,
            on_log=self._on_log
        )
        
        if error:
            messagebox.showerror("Erro", error)
            return
        
        self._log(f"Tarefa {task_id[:8]}... criada")
        self._log("Iniciando processamento...")
        
        # Executar em thread
        thread = threading.Thread(
            target=self._process_worker,
            daemon=True
        )
        thread.start()
    
    def _process_worker(self):
        """Worker que simula processamento com progresso"""
        try:
            total_items = 50
            
            for i in range(total_items):
                # Verificar cancelamento
                if self.execution.is_cancelled():
                    self._log("⚠ Cancelado pelo usuário")
                    return
                
                # Atualizar progresso
                percent = int((i / total_items) * 100)
                self.execution.update_progress(
                    percent,
                    f"Processando item {i+1}/{total_items}"
                )
                
                self._log(f"Item {i+1}/{total_items} - {percent}%")
                
                # Simular trabalho
                time.sleep(0.2)
            
            # Finalizar
            self.execution.update_progress(100, "Concluído!")
            self._log("✓ Processamento concluído com sucesso!")
            
            self.execution.complete({
                "total_items": total_items,
                "status": "success"
            })
            
        except Exception as e:
            self.execution.fail(str(e))
            self._log(f"✕ Erro: {e}")
    
    def _on_progress(self, percent: int, message: str):
        """Callback de progresso"""
        self.after(0, lambda: self._update_progress_ui(percent, message))
    
    def _update_progress_ui(self, percent: int, message: str):
        """Atualiza UI local"""
        self.progress_bar.set(percent / 100)
        self.status_label.configure(text=f"{message} ({percent}%)")
    
    def _on_log(self, message: str):
        """Callback de log"""
        self.after(0, lambda: self._log(message))
    
    def _log(self, message: str):
        """Adiciona mensagem ao log"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


class DemoApp(ctk.CTk):
    """Aplicação de demonstração"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Demo: Sistema de Execução Paralela")
        self.geometry("700x600")
        
        ctk.set_appearance_mode("dark")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Criar gerenciador
        self.execution_manager = get_execution_manager()
        
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color=config.Colors.BACKGROUND)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="Demo: Execução Paralela com Persistência",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=config.Colors.PRIMARY
        )
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # Tabs container
        container = ctk.CTkFrame(main_frame, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # Criar 2 ferramentas de exemplo
        self.ferramenta1 = ExemploFerramentaPage(
            container,
            "Ferramenta A",
            user_id="demo_user"
        )
        self.ferramenta1.grid(row=0, column=0, sticky="nsew")
        
        # Footer com info
        footer = ctk.CTkFrame(main_frame, fg_color=config.Colors.CARD)
        footer.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        
        info_text = (
            "✓ Execute múltiplas ferramentas em paralelo\n"
            "✓ O progresso é persistido automaticamente\n"
            "✓ Saia e volte para ver o progresso mantido"
        )
        info_label = ctk.CTkLabel(
            footer,
            text=info_text,
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            justify="left"
        )
        info_label.pack(padx=20, pady=15)


if __name__ == "__main__":
    app = DemoApp()
    app.mainloop()
