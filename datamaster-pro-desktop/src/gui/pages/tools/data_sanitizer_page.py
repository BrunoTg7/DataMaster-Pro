"""
Data Sanitizer Page - Limpa e normaliza dados de planilhas
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.data_sanitizer.data_sanitizer_v2 import DataSanitizer
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.global_executor import global_executor



class DataSanitizerPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.sanitizer = DataSanitizer(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        self.execution = ExecutionHelper("data_sanitizer", "Data Sanitizer", user_id)
        super().__init__(master, "data_sanitizer", "Data Sanitizer", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.task_helper = TaskHelper("data_sanitizer")
        self.input_file = None
        self.df = None
        self.detected_fields = {}

    def _check_task_state(self):
        from src.core.storage.storage_manager import StorageManager
        storage = StorageManager()
        last_task = storage.get_last_task_by_tool("data_sanitizer")
        
        if not last_task:
            return
        
        status = last_task.get("status")
        
        if status == "running":
            if hasattr(self, 'progress_frame'):
                self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
            if hasattr(self, 'progress_bar'):
                progress = last_task.get("progress_percent", 0)
                self.progress_bar.set(progress / 100)
            if hasattr(self, 'progress_label'):
                message = last_task.get("progress_message", "Processando...")
                self.progress_label.configure(text=message)
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="⏳ Tarefa em andamento...")
            
        elif status == "completed":
            rows = last_task.get("rows_processed", 0)
            if hasattr(self, 'status_label'):
                self.status_label.configure(text=f"✅ Última execução concluída ({rows} registros)")
            
        elif status == "interrupted":
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="⚠️ Tarefa anterior interrompida.")
            
        elif status == "failed":
            error = last_task.get("error_message", "Erro")
            if hasattr(self, 'status_label'):
                self.status_label.configure(text=f"❌ Última execução falhou")

    def _log_from_thread(self, message: str):
        self.after(0, lambda: self._add_log_safe(message))

    def _add_log_safe(self, message: str):
        try:
            if hasattr(self, 'results_text') and self.results_text.winfo_exists():
                self.results_text.configure(state="normal")
                self.results_text.insert("end", f"• {message}\n")
                self.results_text.see("end")
                self.results_text.configure(state="disabled")
        except Exception:
            pass

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Carregue uma planilha suja (CPF sem pontos, nomes minúsculos, endereços bagunçados) e normalize tudo automaticamente.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        input_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl = ctk.CTkLabel(
            input_frame,
            text="Arquivo de entrada (CSV ou Excel):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.file_btn = ctk.CTkButton(
            input_frame,
            text="Selecionar Arquivo",
            command=self._select_file,
            fg_color=config.Colors.PRIMARY,
            width=200
        )
        self.file_btn.pack(anchor="w", padx=20, pady=(0, 10))

        self.file_label = ctk.CTkLabel(
            input_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file_label.pack(anchor="w", padx=20, pady=(0, 15))

        options_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        options_frame.pack(fill="x", padx=20, pady=10)

        lbl_options = ctk.CTkLabel(
            options_frame,
            text="Campos a Normalizar:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl_options.pack(anchor="w", padx=20, pady=(15, 10))

        self.check_vars = {}
        
        fields = [
            ("nome", "Nomes (maiúsculas + removes acentos)"),
            ("cpf", "CPF (formato: 000.000.000-00)"),
            ("cnpj", "CNPJ (formato: 00.000.000/0000-00)"),
            ("telefone", "Telefones ((00) 00000-0000)"),
            ("cep", "CEP (formato: 00000-000)"),
            ("email", "E-mails (lowercase)"),
            ("endereco", "Endereços (abreviações padronizadas)"),
        ]
        
        for field, label in fields:
            var = ctk.BooleanVar(value=True)
            self.check_vars[field] = var
            
            cb = ctk.CTkCheckBox(
                options_frame,
                text=label,
                variable=var,
                font=ctk.CTkFont(size=12)
            )
            cb.pack(anchor="w", padx=20, pady=2)

        select_all_btn = ctk.CTkButton(
            options_frame,
            text="Selecionar Todos",
            command=self._select_all,
            fg_color="transparent",
            border_width=1,
            width=120
        )
        select_all_btn.pack(anchor="w", padx=20, pady=(10, 15))

        # Tema Visual da Planilha
        theme_frame = ctk.CTkFrame(content, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(5, 5))

        ctk.CTkLabel(
            theme_frame,
            text="Tema Visual da Planilha (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(5, 5))

        self.visual_theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Azul Corporativo", "Verde Esmeralda", "Laranja Moderno", "Cinza Minimalista"],
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER
        )
        self.visual_theme_menu.set("Azul Corporativo")
        self.visual_theme_menu.pack(anchor="w", pady=(0, 10))

        self.action_btn = self._create_action_button(content, "Limpar e Normalizar", self._run_sanitization)

        self.progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_frame.pack_forget()

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.progress_label.pack()

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=400,
            height=8
        )
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        results_label = ctk.CTkLabel(
            content,
            text="Preview (primeiras 5 linhas):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        results_label.pack(anchor="w", padx=20, pady=(10, 5))

        self.results_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.results_text = ctk.CTkTextbox(
            self.results_frame,
            width=500,
            height=180,
            font=ctk.CTkFont(size=11)
        )
        self.results_text.pack(padx=20, pady=20, fill="both", expand=True)
        self.results_text.insert("1.0", "Carregue um arquivo para ver o preview...\n")
        self.results_text.configure(state="disabled")

    def _select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=[
                ("Arquivos Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        if file_path:
            self.input_file = file_path
            self.file_label.configure(text=os.path.basename(file_path))
            
            try:
                if file_path.endswith('.xlsx'):
                    self.df = pd.read_excel(file_path)
                else:
                    self.df = pd.read_csv(file_path, encoding='utf-8')
                
                self.detected_fields = self.sanitizer.detect_fields(self.df)
                
                self.results_text.configure(state="normal")
                self.results_text.delete("1.0", "end")
                
                preview = f"Arquivo carregado: {len(self.df)} linhas, {len(self.df.columns)} colunas\n\n"
                preview += f"Campos detectados:\n"
                
                for field, col in self.detected_fields.items():
                    preview += f"  - {field}: {col}\n"
                
                preview += f"\nPrimeiras 5 linhas:\n"
                preview += self.df.head().to_string()
                
                self.results_text.insert("1.0", preview)
                self.results_text.configure(state="disabled")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo: {e}")

    def _select_all(self):
        for var in self.check_vars.values():
            var.set(True)

    def _run_sanitization(self):
        task_id, error = self.task_helper.start_task({})
        if error:
            messagebox.showwarning("Aviso", error)
            return

        if not self.input_file:
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo primeiro")
            return

        options = {field: var.get() for field, var in self.check_vars.items()}
        
        if not any(options.values()):
            messagebox.showwarning("Aviso", "Selecione pelo menos um campo para normalizar")
            return

        save_path = filedialog.asksaveasfilename(
            title="Salvar arquivo limpo",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel", "*.xlsx"),
                ("CSV", "*.csv")
            ]
        )
        
        if not save_path:
            return

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))

        theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
        visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

        input_file = self.input_file
        sanitizer = self.sanitizer
        global_executor.submit(
            execute_func=lambda: sanitizer.process_file(input_file, save_path, options, visual_theme=visual_theme),
            on_complete=lambda result: self.after(0, lambda: self._show_results(result)),
            tool_name="data_sanitizer",
            tool_display_name="Data Sanitizer",
            user_id=self.user_id
        )

    def _show_results(self, result):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        
        if result.get("success"):
            self.results_text.configure(state="normal")
            self.results_text.delete("1.0", "end")
            
            summary = f"""LIMPEZA CONCLUÍDA
{'='*40}
Linhas processadas: {result.get('total_rows', 0)}
Campos normalizados: {result.get('fields_processed', 0)}

Alterações por campo:
"""
            changes = result.get("changes", {})
            for field, count in changes.items():
                summary += f"  - {field}: {count} registros\n"
            
            summary += f"\nArquivo salvo em:\n{result.get('output_path', '')}"
            
            self.results_text.insert("1.0", summary)
            self.results_text.configure(state="disabled")
            
            rows = result.get('total_rows', 0)
            save_path = result.get('output_path', '')
            self._finalize_execution(result, save_path, rows, {"registros": rows})
            messagebox.showinfo("Sucesso", f"Arquivo limpo e salvo com sucesso!\n{rows} linhas processadas.")
        else:
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

    def _show_error(self, error):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro na limpeza: {error}")
        self._finalize_execution({"success": False, "error": error}, "")

    def _update_progress(self, value):
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(value / 100)
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=f"Normalizando... {value}%")
        except Exception:
            pass
        self.task_helper.update_progress(value, 100, value)
        self.task_helper.add_log(f"Normalizando... {value}%")