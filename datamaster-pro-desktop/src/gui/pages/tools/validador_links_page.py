"""
Validador de Links Page - Verifica se links estão ativos e produtos disponíveis
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.validador_links.validador_links_v2 import ValidadorLinks
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.global_executor import global_executor


class ValidadorLinksPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.validador = ValidadorLinks(
            progress_callback=self._update_progress
        )
        self.execution = ExecutionHelper("validador_links", "Validador de Links", user_id)
        super().__init__(master, "validador_links", "Validador de Links", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.task_helper = TaskHelper("validador_links")
        self.urls = []
        self._last_result_text = ""

    def _check_task_state(self):
        from src.core.storage.storage_manager import StorageManager
        storage = StorageManager()
        last_task = storage.get_last_task_by_tool("validador_links")
        
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

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Cole URLs de produtos para verificar se estão ativas e disponíveis em estoque.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        input_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl = ctk.CTkLabel(
            input_frame,
            text="URLs (uma por linha):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.text_area = ctk.CTkTextbox(
            input_frame,
            width=500,
            height=150,
            font=ctk.CTkFont(size=12)
        )
        self.text_area.pack(padx=20, pady=(0, 15))

        self.drop_frame = self._create_drop_zone(
            content,
            "Selecione arquivo com URLs",
            self._select_file
        )

        self.file_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file_label.pack(pady=5)

        self.action_btn = self._create_action_button(content, "Validar Links", self._run_validation)

        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)

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

        self.results_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.results_text = ctk.CTkTextbox(
            self.results_frame,
            width=500,
            height=200,
            font=ctk.CTkFont(size=11)
        )
        self.results_text.pack(padx=20, pady=20, fill="both", expand=True)
        self.results_text.insert("1.0", "Resultados aparecerão aqui...\n")
        self.results_text.configure(state="disabled")

        self.viewer_btn = ResultViewerButton(
            self,
            content,
            lambda: self._last_result_text if hasattr(self, '_last_result_text') else "",
            "👁️ Visualizar"
        )
        self.viewer_btn.pack(pady=(0, 15))

    def _select_file(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=[("Arquivos de texto", "*.txt"), ("CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.file_label.configure(text=os.path.basename(file_path))
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_area.delete("1.0", "end")
                    self.text_area.insert("1.0", content)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler arquivo: {e}")

    def _run_validation(self):
        task_id, error = self.task_helper.start_task({})
        if error:
            messagebox.showwarning("Aviso", error)
            return

        text = self.text_area.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Aviso", "Por favor, insira pelo menos uma URL")
            self.task_helper.cancel()
            return

        self.urls = [line.strip() for line in text.split('\n') if line.strip()]

        if not self.urls:
            messagebox.showwarning("Aviso", "Nenhuma URL válida encontrada")
            self.task_helper.cancel()
            return

        from src.tools.minerador.minerador_v2 import validate_url
        invalid = [u for u in self.urls if not validate_url(u)]
        if invalid:
            msg = "URLs inválidas ignoradas:\n" + "\n".join(invalid[:5])
            if len(invalid) > 5:
                msg += f"\n...e mais {len(invalid) - 5}"
            messagebox.showwarning("URLs Inválidas", msg)
        self.urls = [u for u in self.urls if validate_url(u)]
        if not self.urls:
            self.task_helper.cancel()
            return

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"Iniciando validação de {len(self.urls)} URLs...\n\n")
        self.results_text.configure(state="disabled")

        urls = self.urls
        validador = self.validador
        def execute_func():
            result = validador.validate_links(urls)
            return result
        def on_complete(result):
            self.after(0, lambda: self._show_results(result))
        global_executor.submit(
            execute_func=execute_func,
            on_complete=on_complete,
            tool_name="validador_links",
            tool_display_name="Validador de Links",
            user_id=self.user_id
        )

    def _validation_worker(self):
        try:
            result = self.validador.validate_links(self.urls)
            self.after(0, lambda: self._show_results(result) if hasattr(self, 'winfo_exists') and self.winfo_exists() else None)
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)) if hasattr(self, 'winfo_exists') and self.winfo_exists() else None)

    def _show_results(self, result):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")

        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")

        summary_data = result.get('summary', {})
        summary = f"""📊 RELATÓRIO PROFISSIONAL DE VALIDAÇÃO
{'='*45}
✅ Ativos: {summary_data.get('active', 0)}
❌ Quebrados: {summary_data.get('broken', 0)}
📦 Esgotados: {summary_data.get('out_of_stock', 0)}
🛡️ Restritos: {summary_data.get('restricted', 0)}
{'='*45}
Total Processado: {summary_data.get('total', 0)}
\n"""
        self.results_text.insert("1.0", summary)

        full_result = summary
        for r in result.get('results', []):
            status_type = r.get('status_type', 'unknown')

            if status_type == "active":
                icon = "✅"
            elif status_type == "out_of_stock":
                icon = "📦"
            elif status_type == "restricted":
                icon = "🛡️"
            else:
                icon = "❌"

            title = r.get('title', 'Sem título')
            url = r.get('url', '')
            msg = r.get('message', '')

            line = f"{icon} {title[:50]}...\n"
            self.results_text.insert("end", line)
            self.results_text.insert("end", f"   URL: {url[:70]}\n")
            self.results_text.insert("end", f"   Status: {msg}\n\n")

            full_result += line + f"   URL: {url[:70]}\n   Status: {msg}\n\n"

        self._last_result_text = full_result

        self.results_text.configure(state="disabled")

        msg = f"Validação concluída!\n{summary_data.get('active', 0)} links ativos de {summary_data.get('total', 0)}"
        messagebox.showinfo("Concluído", msg)
        total = summary_data.get('total', 0)
        self._finalize_execution({"success": True}, "", total, {"urls_validadas": total, "ativas": summary_data.get('active', 0)})

    def _show_error(self, error):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro na validação: {error}")
        self._finalize_execution({"success": False, "error": error}, "")

    def _update_progress(self, value):
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(value / 100)
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=f"Validando... {value}%")
        except Exception:
            pass