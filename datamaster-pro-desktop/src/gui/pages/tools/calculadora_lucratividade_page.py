"""
Calculadora de Lucratividade Page - Calcula margem de lucro e identifica oportunidades de arbitragem
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor



class CalculadoraLucratividadePage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.calculadora = CalculadoraLucratividade(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        self.execution = ExecutionHelper("calculadora_lucratividade", "Calculadora de Lucratividade", user_id)
        super().__init__(master, "calculadora_lucratividade", "Calculadora de Lucratividade", on_back, execution_tracker, user_id)
        self._check_task_state()
        self._last_result_text = ""

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("calculadora_lucratividade")
        
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
        self.after(0, lambda: self._add_log(message))

    def _add_log(self, message: str):
        """Adiciona mensagem de log à área de resultados ou log"""
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
            text="Defina seu custo e compare preços em múltiplos concorrentes para encontrar oportunidades de arbitragem.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        input_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl_cost = ctk.CTkLabel(
            input_frame,
            text="Preço de Custo (R$):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_cost.pack(anchor="w", padx=20, pady=(15, 5))

        self.cost_entry = ctk.CTkEntry(
            input_frame,
            width=200,
            placeholder_text="Ex: 50.00",
            font=ctk.CTkFont(size=12)
        )
        self.cost_entry.pack(anchor="w", padx=20, pady=(0, 10))

        lbl_urls = ctk.CTkLabel(
            input_frame,
            text="URLs de concorrentes (uma por linha):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_urls.pack(anchor="w", padx=20, pady=(5, 5))

        self.text_area = ctk.CTkTextbox(
            input_frame,
            width=500,
            height=120,
            font=ctk.CTkFont(size=12)
        )
        self.text_area.pack(padx=20, pady=(0, 15))

        self.action_btn = self._create_action_button(content, "Calcular Lucratividade", self._run_calculation)

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
            text="Resultados:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        results_label.pack(anchor="w", padx=20, pady=(10, 5))

        self.results_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.results_text = ctk.CTkTextbox(
            self.results_frame,
            width=500,
            height=280,
            font=ctk.CTkFont(size=11)
        )
        self.results_text.pack(padx=20, pady=20, fill="both", expand=True)
        self.results_text.insert("1.0", "Resultados aparecerão aqui...\n")
        self.results_text.configure(state="disabled")

        self.viewer_btn = ResultViewerButton(
            self,
            content,
            lambda: self._last_result_text if hasattr(self, '_last_result_text') else "",
            "👁️ Visualizar Relatório"
        )
        self.viewer_btn.pack(pady=(0, 15))

    def _run_calculation(self):
        cost_text = self.cost_entry.get().strip()
        if not cost_text:
            messagebox.showwarning("Aviso", "Por favor, insira o preço de custo")
            return
        
        try:
            cost_price = float(cost_text.replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro", "Preço de custo inválido")
            return
        
        text = self.text_area.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Aviso", "Por favor, insira pelo menos uma URL de concorrente")
            return

        urls = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not urls:
            messagebox.showwarning("Aviso", "Nenhuma URL válida encontrada")
            return

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", f"Calculando lucratividade para custo de R$ {cost_price:.2f}...\n\n")
        self.results_text.configure(state="disabled")

        calculadora = self.calculadora
        def execute_func():
            result = calculadora.calculate(cost_price, urls)
            return result
        def on_complete(result):
            self.after(0, lambda: self._show_results(result))
        task_executor.submit(
            execute_func=execute_func,
            on_complete=on_complete,
            tool_name="calculadora_lucratividade",
            tool_display_name="Calculadora de Lucratividade",
            user_id=self.user_id
        )

    def _calculation_worker(self, cost_price, urls):
        try:
            result = self.calculadora.calculate(cost_price, urls)
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
        
        if not result.get("success"):
            self.results_text.insert("1.0", f"❌ Erro: {result.get('error', 'Falha na captura de preços')}\n")
            self.results_text.configure(state="disabled")
            return
        
        results = result.get("results", [])
        best = result.get("best_opportunity")
        cost = result.get("cost_price", 0)
        
        header = f"""💰 RELATÓRIO DE LUCRATIVIDADE v3.0 Pro
{'='*45}
Preço de Custo: R$ {cost:.2f}
Data da Análise: {result.get('timestamp')}
Status: {len(results)} concorrentes analisados com sucesso.
\n"""
        self.results_text.insert("1.0", header)
        
        if best:
            self.results_text.insert("end", f"🔥 MELHOR OPORTUNIDADE:\n")
            self.results_text.insert("end", f"   Local: {best['site'].upper()}\n")
            self.results_text.insert("end", f"   Venda: R$ {best['price']:.2f} | Lucro Líquido: R$ {best['net_profit']:.2f}\n")
            self.results_text.insert("end", f"   ROI: {best['roi']}% | Margem: {best['margin']}%\n")
            self.results_text.insert("end", f"   Score: {best['opportunity_score']}/100\n\n")
        
        self.results_text.insert("end", f"📊 DETALHAMENTO DE CONCORRENTES:\n{'='*45}\n\n")
        
        full_report = header + "📌 SUMÁRIO EXECUTIVO:\n" + result.get('summary', '') + "\n\n"
        
        for i, res in enumerate(results, 1):
            icon = "✅" if res['net_profit'] > 0 else "⚠️"
            line = f"{i}. {res['site'].upper()} - R$ {res['price']:.2f}\n"
            metrics = f"   {icon} Lucro: R$ {res['net_profit']:.2f} | ROI: {res['roi']}% | Taxas: R$ {res['marketplace_tax']}\n\n"
            
            self.results_text.insert("end", line)
            self.results_text.insert("end", metrics)
            full_report += line + metrics

        self._last_result_text = full_report
        self.results_text.configure(state="disabled")
        
        result = {"success": True}
        rows = len(results)
        if best and best['net_profit'] > 0:
            messagebox.showinfo("Sucesso", f"Oportunidade encontrada!\nROI de {best['roi']}% em {best['site'].upper()}")
        else:
            messagebox.showwarning("Aviso", "Margens baixas detectadas para este produto.")
        self._finalize_execution(result, "", rows, {"oportunidades": rows})

    def _show_error(self, error):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro no cálculo: {error}")
        self._finalize_execution({"success": False, "error": error}, "")

    def _update_progress(self, value):
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(value / 100)
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=f"Buscando preços... {value}%")
        except Exception:
            pass
