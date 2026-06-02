"""
Extrator de Reviews Page - Extrai e analisa sentimento de reviews de marketplaces
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.extrator_reviews.extrator_reviews_v2 import ExtratorReviews
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor



class ExtratorReviewsPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.extrator = ExtratorReviews(
            _p0=config._r1(),
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        self.execution = ExecutionHelper("extrator_reviews", "Extrator de Reviews", user_id)
        super().__init__(master, "extrator_reviews", "Extrator de Reviews", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.urls = []
        self._last_result_text = ""

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("extrator_reviews")
        
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
        if "Erro" not in message:
            self.after(0, lambda: self._update_log_display(message))
    
    def _update_log_display(self, message: str):
        try:
            if hasattr(self, 'log_text') and self.log_text and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", f"• {message}\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            pass

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Cole URLs de produtos do Mercado Livre, Amazon ou Shopee para extrair reviews e analisar sentimento.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        input_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl = ctk.CTkLabel(
            input_frame,
            text="URLs de produtos (uma por linha):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.text_area = ctk.CTkTextbox(
            input_frame,
            width=500,
            height=120,
            font=ctk.CTkFont(size=12)
        )
        self.text_area.pack(padx=20, pady=(0, 15))

        self.action_btn = self._create_action_button(content, "Analisar Reviews", self._run_analysis)

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
            text="Resultados da Análise:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        results_label.pack(anchor="w", padx=20, pady=(10, 5))

        self.results_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.results_text = ctk.CTkTextbox(
            self.results_frame,
            width=500,
            height=250,
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

    def _run_analysis(self):
        text = self.text_area.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Aviso", "Por favor, insira pelo menos uma URL de produto")
            return

        self.urls = [line.strip() for line in text.split('\n') if line.strip()]

        if not self.urls:
            messagebox.showwarning("Aviso", "Nenhuma URL válida encontrada")
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
            return

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"Iniciando análise de {len(self.urls)} produtos...\n\n")
        self.results_text.configure(state="disabled")

        urls = self.urls
        extrator = self.extrator
        def execute_func():
            result = extrator.analyze_multiple(urls)
            return result
        def on_complete(result):
            self.after(0, lambda: self._show_results(result))
        task_executor.submit(
            execute_func=execute_func,
            on_complete=on_complete,
            tool_name="extrator_reviews",
            tool_display_name="Extrator de Reviews",
            user_id=self.user_id
        )

    def _analysis_worker(self):
        try:
            result = self.extrator.analyze_multiple(self.urls)
            self.after(0, lambda r=result: self._show_results(r) if hasattr(self, 'winfo_exists') and self.winfo_exists() else None)
        except Exception as e:
            err = str(e)
            if self.log_callback:
                self.log_callback(f"Erro: {err}")
            self.after(0, lambda err=err: self._show_error(err) if hasattr(self, 'winfo_exists') and self.winfo_exists() else None)

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

        summary = f"""📊 RESUMO DA ANÁLISE
{'='*40}
Total de produtos: {result.get('total', 0)}
Analisados com sucesso: {result.get('analyzed', 0)}

"""
        self.results_text.insert("1.0", summary)

        full_result = summary
        for r in result.get("results", []):
            if not r.get("success"):
                self.results_text.insert("end", f"❌ {r.get('url', 'URL')[:50]}...\n   Erro: {r.get('error', 'Erro desconhecido')}\n\n")
                full_result += f"❌ {r.get('url', 'URL')[:50]}...\n   Erro: {r.get('error', 'Erro desconhecido')}\n\n"
                continue

            sentiment_emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(r.get("sentiment", "neutral"), "😐")

            line = f"""{sentiment_emoji} {r.get('site', 'Site')} - {r.get('total_reviews', 0)} reviews
   Sentimento: {r.get('sentiment', 'unknown').upper()} (score: {r.get('score', 0)}%)
   Positivos: {r.get('positive', 0)} | Negativos: {r.get('negative', 0)} | Neutros: {r.get('neutral', 0)}

"""
            self.results_text.insert("end", line)
            full_result += line

        self._last_result_text = full_result

        self.results_text.configure(state="disabled")

        positive_count = sum(1 for r in result.get("results", []) if r.get("sentiment") == "positive")
        analyzed = result.get("analyzed", 0)
        self._finalize_execution(result, "", analyzed, {"reviews": analyzed})
        messagebox.showinfo("Concluído", f"Análise concluída!\n{positive_count} produtos com sentimento positivo")

    def _show_error(self, error):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro na análise: {error}")
        self._finalize_execution({"success": False, "error": error}, "")

    def _update_progress(self, value):
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(value / 100)
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=f"Analisando... {value}%")
        except Exception:
            pass
