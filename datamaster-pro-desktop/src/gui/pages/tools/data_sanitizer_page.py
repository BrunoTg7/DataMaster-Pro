"""
Data Sanitizer Page - Limpa e normaliza dados de planilhas
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys
import threading
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.data_sanitizer.data_sanitizer_v2 import DataSanitizer
from src.gui.components.result_viewer_modal import ResultViewerButton


class DataSanitizerPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.sanitizer = DataSanitizer(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        super().__init__(master, "data_sanitizer", "Data Sanitizer", on_back, execution_tracker, user_id)
        self.input_file = None
        self.df = None
        self.detected_fields = {}

    def _log_from_thread(self, message: str):
        self.after(0, lambda: self._add_log(message))

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

        thread = threading.Thread(target=self._sanitization_worker, args=(save_path, options), daemon=True)
        thread.start()

    def _sanitization_worker(self, output_path, options):
        try:
            result = self.sanitizer.process_file(self.input_file, output_path, options)
            self.after(0, lambda: self._show_results(result))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    def _show_results(self, result):
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
            
            messagebox.showinfo("Sucesso", f"Arquivo limpo e salvo com sucesso!\n{result.get('total_rows', 0)} linhas processadas.")
        else:
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

    def _show_error(self, error):
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro na limpeza: {error}")

    def _update_progress(self, value):
        self.progress_bar.set(value / 100)
        self.progress_label.configure(text=f"Normalizando... {value}%")