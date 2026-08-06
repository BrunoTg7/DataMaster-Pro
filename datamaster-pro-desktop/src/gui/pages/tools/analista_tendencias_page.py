"""
Analista de Tendências Page - Trend Intelligence Enterprise
Zero Scraping — APIs Oficiais + Fontes Legítimas
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.analista_tendencias import AnalistaTendenciasEnterprise
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor

class AnalistaTendenciasPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        # Criar primeiro para obter niches disponíveis
        temp_analista = AnalistaTendenciasEnterprise()
        self.niches_disponiveis = temp_analista.get_available_niches()
        self.active_sources = temp_analista.get_active_sources()
        
        # Agora criar com callbacks
        self.analista = AnalistaTendenciasEnterprise(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        self.execution = ExecutionHelper("analista_tendencias", "Analista de Tendências Enterprise", user_id)
        super().__init__(master, "analista_tendencias", "Analista de Tendências Enterprise", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.results_for_copy = ""
        self._check_provider_status()

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("analista_tendencias")
        
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

    def _check_provider_status(self):
        """Verifica quais providers estão configurados e alerta o usuário"""
        if not self.active_sources:
            self.after(1000, lambda: messagebox.showinfo(
                "Configuração Necessária",
                "⚠️ Nenhuma fonte de tendências configurada!\n\n"
                "Para usar o Analista Enterprise, configure no .env:\n\n"
                "📊 Google Trends (sempre ativo via pytrends):\n"
                "   Funciona sem credenciais (limite ~100 req/hora)\n\n"
                "🛍️ Mercado Livre Bestsellers API (Obrigatório para dados de venda):\n"
                "   ML_CLIENT_ID=seu_client_id\n"
                "   ML_CLIENT_SECRET=seu_client_secret\n\n"
                "🎵 TikTok Creative Center (Export manual CSV):\n"
                "   Coloque CSVs exportados em data/tiktok_trends/\n\n"
                "🚀 Exploding Topics API (Pago, opcional):\n"
                "   EXPLODING_TOPICS_API_KEY=sua_chave\n\n"
                "Obtenha credenciais ML em: https://developers.mercadolivre.com.br"
            ))
        else:
            self._log_from_thread(f"✅ Fontes ativas: {', '.join(self.active_sources)}")

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        sources_info = f"Fontes ativas: {', '.join(self.active_sources) if self.active_sources else 'Apenas Google Trends (sem credenciais ML)'}"
        
        info = ctk.CTkLabel(
            content,
            text=(
                f"Trend Intelligence Enterprise — Zero Scraping\n"
                f"Fontes: Google Trends API + ML Bestsellers API + TikTok CSV + Exploding Topics (opcional)\n\n"
                f"{sources_info}\n\n"
                f"Selecione um nicho para identificar produtos em alta tendência."
            ),
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=550,
            justify="left"
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

        self.results_text = ctk.CTkTextbox(content, height=350, font=ctk.CTkFont(size=11))
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

        analista = self.analista
        def execute_func():
            result = analista.analyze(niche_key, search_term)
            return result
        def on_complete(result):
            self.after(0, lambda: self._show_results(result))
        task_executor.submit(
            execute_func=execute_func,
            on_complete=on_complete,
            tool_name="analista_tendencias",
            tool_display_name="Analista de Tendências",
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
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        
        if not result.get("success"):
            self.results_text.insert("1.0", f"❌ Erro: {result.get('error')}\n")
            self.results_text.configure(state="disabled")
            return
        
        trends = result.get("trends", [])
        sources = result.get("sources_used", [])
        
        header = f"""🔥 TREND INTELLIGENCE ENTERPRISE v2.0
{'='*55}
Nicho: {result.get('niche')}
Data: {result.get('timestamp')}
Fontes Ativas: {', '.join(sources) if sources else 'Nenhuma'}
{result.get('summary')}

"""
        self.results_text.insert("1.0", header)
        
        copy_text = header
        for i, trend in enumerate(trends, 1):
            growth = trend.get('growth', '0%')
            score = trend.get('score', 0)
            opportunity = trend.get('opportunity', 'Baixa')
            platforms = ', '.join(trend.get('platforms', []))
            mentions = trend.get('mentions', 0)
            
            line = f"""{i}. {trend['product']}
   🎯 Oportunidade: {opportunity}  |  Score: {score}/100  |  Crescimento: {growth}
   📊 Plataformas: {platforms}  |  Sinais: {mentions}
   ---
"""
            self.results_text.insert("end", line)
            copy_text += line
        
        self.results_for_copy = copy_text
        self.results_text.configure(state="disabled")
        self._finalize_execution({"success": True}, "", len(trends), {"tendencias": len(trends), "fontes": sources})
        messagebox.showinfo("Sucesso", f"Análise Enterprise concluída!\n{len(trends)} tendências detectadas\nFontes: {', '.join(sources) if sources else 'Nenhuma configurada'}")

    def _show_error(self, error):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Falha na análise: {error}")
        self._finalize_execution({"success": False, "error": error}, "")

    def _update_progress(self, value):
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(value / 100)
        except Exception:
            pass
