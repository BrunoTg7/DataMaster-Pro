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


class ExtratorReviewsPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.extrator = ExtratorReviews(
            api_key=config.SCRAPERAPI_KEY,
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        super().__init__(master, "extrator_reviews", "Extrator de Reviews", on_back, execution_tracker, user_id)
        self.urls = []
        self._last_result_text = ""

    def _log_from_thread(self, message: str):
        if "Erro" not in message:
            self.after(0, lambda: self._update_log_display(message))
    
    def _update_log_display(self, message: str):
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"• {message}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

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

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"Iniciando análise de {len(self.urls)} produtos...\n\n")
        self.results_text.configure(state="disabled")

        thread = threading.Thread(target=self._analysis_worker, daemon=True)
        thread.start()

    def _analysis_worker(self):
        try:
            result = self.extrator.analyze_multiple(self.urls)
            self.after(0, lambda r=result: self._show_results(r))
        except Exception as e:
            err = str(e)
            if self.log_callback:
                self.log_callback(f"Erro: {err}")
            self.after(0, lambda err=err: self._show_error(err))

    def _show_results(self, result):
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
        messagebox.showinfo("Concluído", f"Análise concluída!\n{positive_count} produtos com sentimento positivo")

    def _show_error(self, error):
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro na análise: {error}")

    def _update_progress(self, value):
        self.progress_bar.set(value / 100)
        self.progress_label.configure(text=f"Analisando... {value}%")