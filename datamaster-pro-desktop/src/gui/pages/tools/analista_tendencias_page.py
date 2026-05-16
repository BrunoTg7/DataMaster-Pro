"""
Analista de Tendências Page - Identifica produtos trending em nichos específicos
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import threading

# Garante que o caminho do projeto esteja no sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.analista_tendencias.analista_tendencias_v2 import AnalistaTendencias
from src.gui.components.result_viewer_modal import ResultViewerButton

class AnalistaTendenciasPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        # Criar primeiro para obter niches disponíveis
        temp_analista = AnalistaTendencias()
        self.niches_disponiveis = temp_analista.get_available_niches()
        
        # Agora criar com callbacks
        self.analista = AnalistaTendencias(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        super().__init__(master, "analista_tendencias", "Analista de Tendências", on_back, execution_tracker, user_id)
        self.results_for_copy = ""

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
            text="Selecione um nicho para identificar produtos em alta tendência via Redes Sociais e Marketplaces.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        input_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl_niche = ctk.CTkLabel(
            input_frame,
            text="Selecione o Nicho:",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_niche.pack(anchor="w", padx=20, pady=(15, 5))

        niche_options = [n["name"] for n in self.niches_disponiveis]
        self.niche_combo = ctk.CTkComboBox(input_frame, values=niche_options, width=300)
        self.niche_combo.pack(anchor="w", padx=20, pady=(0, 10))
        if niche_options: self.niche_combo.set(niche_options[0])

        lbl_search = ctk.CTkLabel(input_frame, text="Termo específico (opcional):", font=ctk.CTkFont(size=12))
        lbl_search.pack(anchor="w", padx=20, pady=(10, 5))

        self.search_entry = ctk.CTkEntry(input_frame, width=300, placeholder_text="Ex: Creatina, Fone, etc")
        self.search_entry.pack(anchor="w", padx=20, pady=(0, 15))

        self.action_btn = self._create_action_button(content, "Analisar Tendências", self._run_analysis)

        self.progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_frame.pack_forget()

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        self.log_text = ctk.CTkTextbox(content, height=100, font=ctk.CTkFont(size=10))
        self.log_text.pack(fill="x", padx=20, pady=10)
        self.log_text.insert("1.0", "Aguardando análise...\n")
        self.log_text.configure(state="disabled")

        self.results_text = ctk.CTkTextbox(content, height=300, font=ctk.CTkFont(size=11))
        self.results_text.pack(fill="both", expand=True, padx=20, pady=10)
        self.results_text.insert("1.0", "Os resultados aparecerão aqui...\n")
        self.results_text.configure(state="disabled")
        
        self.viewer_btn = ResultViewerButton(
            self,
            content,
            lambda: self.results_for_copy if hasattr(self, 'results_for_copy') else "",
            "👁️ Visualizar Relatório Completo"
        )
        self.viewer_btn.pack(pady=(0, 15))

    def _run_analysis(self):
        selected_name = self.niche_combo.get()
        niche_key = None
        for n in self.niches_disponiveis:
            if n["name"] == selected_name:
                niche_key = n["key"]
                break
        
        if not niche_key:
            messagebox.showwarning("Aviso", "Selecione um nicho válido")
            return
        
        search_term = self.search_entry.get().strip() or None

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"🚀 Iniciando Trend Intelligence em {selected_name}...\n\n")
        self.results_text.configure(state="disabled")

        # Inicia o worker em uma thread separada
        thread = threading.Thread(target=self._analysis_worker, args=(niche_key, search_term), daemon=True)
        thread.start()

    def _analysis_worker(self, niche_key, search_term):
        try:
            result = self.analista.analyze(niche_key, search_term)
            self.after(0, lambda: self._show_results(result))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    def _show_results(self, result):
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        
        if not result.get("success"):
            self.results_text.insert("1.0", f"❌ Erro: {result.get('error')}\n")
            self.results_text.configure(state="disabled")
            return
        
        trends = result.get("trends", [])
        header = f"🔥 RELATÓRIO TREND INTELLIGENCE v3.0\n{'='*45}\nNicho: {result.get('niche')}\nData: {result.get('timestamp')}\n\n"
        self.results_text.insert("1.0", header)
        self.results_text.insert("end", f"📌 SUMÁRIO:\n{result.get('summary')}\n\n")
        
        copy_text = header + f"📌 SUMÁRIO:\n{result.get('summary')}\n\n"
        for i, trend in enumerate(trends, 1):
            line = f"{i}. {trend['product']}\n   Oportunidade: {trend['opportunity']} | Score: {trend['score']}/100\n\n"
            self.results_text.insert("end", line)
            copy_text += line
            
        self.results_for_copy = copy_text
        self.results_text.configure(state="disabled")
        messagebox.showinfo("Sucesso", "Análise de tendências concluída!")

    def _show_error(self, error):
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Falha na análise: {error}")

    def _update_progress(self, value):
        self.progress_bar.set(value / 100)