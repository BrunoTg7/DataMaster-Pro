"""
Comissões Page - Sistema de Cálculo e Geração de Relatórios de Comissões
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.comissoes.comissoes import Comissoes
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.global_executor import global_executor


class ComissoesPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.comissoes = Comissoes(
            log_callback=self._log_msg,
            progress_callback=self._update_progress_safe
        )
        self.task_helper = TaskHelper("comissoes")
        self.execution = ExecutionHelper("comissoes", "Comissões", user_id)
        self.sales_file = ""
        self.result_df = None
        self.ranking = []
        self._last_result_text = ""
        super().__init__(master, "comissoes", "Comissões", on_back, execution_tracker, user_id)
        self._check_task_state()

    def _check_task_state(self):
        from src.core.storage.storage_manager import StorageManager
        storage = StorageManager()
        last_task = storage.get_last_task_by_tool("comissoes")
        
        if not last_task:
            return
        
        status = last_task.get("status")
        
        if status == "running":
            self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
            progress = last_task.get("progress_percent", 0)
            message = last_task.get("progress_message", "Processando...")
            self.progress_bar.set(progress / 100)
            if hasattr(self, 'progress_label'):
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

    def _log_msg(self, msg: str):
        self.after(0, lambda: self._update_log(msg))

    def _update_log(self, msg: str):
        try:
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", f"{msg}\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            pass

    def _update_progress_safe(self, value: int):
        self.task_helper.update_progress(value, 100, value)
        self.after(0, lambda: self._set_progress(value))

    def _set_progress(self, value: int):
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(value / 100)
        except Exception:
            pass

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Calcule comissões de vendedores e gere relatórios individuais em PDF.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        # Drop Zone
        self.drop_frame = self._create_drop_zone(
            content,
            "Arraste a planilha de vendas aqui",
            self._select_file
        )

        self.file_label = ctk.CTkLabel(
            content,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file_label.pack(pady=(0, 10))

        # Regras de Comissão
        rules_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        rules_frame.pack(fill="x", padx=20, pady=10)

        rules_lbl = ctk.CTkLabel(
            rules_frame,
            text="⚙️ Regras de Comissão",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        rules_lbl.pack(anchor="w", padx=20, pady=(15, 10))

        type_frame = ctk.CTkFrame(rules_frame, fg_color="transparent")
        type_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.rule_type_var = ctk.StringVar(value="percentage")

        pct_radio = ctk.CTkRadioButton(
            type_frame, text="% Fixa",
            variable=self.rule_type_var, value="percentage",
            command=self._toggle_rule_type, font=ctk.CTkFont(size=12)
        )
        pct_radio.pack(side="left", padx=(0, 20))

        tiers_radio = ctk.CTkRadioButton(
            type_frame, text="Faixas de Desempenho",
            variable=self.rule_type_var, value="tiers",
            command=self._toggle_rule_type, font=ctk.CTkFont(size=12)
        )
        tiers_radio.pack(side="left")

        # Frame % Fixa
        self.percentage_frame = ctk.CTkFrame(rules_frame, fg_color="transparent")
        self.percentage_frame.pack(fill="x", padx=20, pady=(0, 15))

        pct_lbl = ctk.CTkLabel(
            self.percentage_frame,
            text="Porcentagem da comissão (%):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        pct_lbl.pack(anchor="w", pady=(0, 5))

        self.percentage_entry = ctk.CTkEntry(
            self.percentage_frame, width=120, placeholder_text="Ex: 5"
        )
        self.percentage_entry.insert(0, "5")
        self.percentage_entry.pack(anchor="w")

        # Frame Faixas
        self.tiers_frame = ctk.CTkFrame(rules_frame, fg_color="transparent")
        self.tiers_frame.pack_forget()

        tier_note = ctk.CTkLabel(
            self.tiers_frame,
            text="Exemplo: Até R$ 10.000 = 3%, acima = 5%",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        tier_note.pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(self.tiers_frame, text="Faixa 1 (% até limite):", font=ctk.CTkFont(size=11),
                      text_color=config.Colors.TEXT_SECONDARY).pack(anchor="w", pady=(5, 2))
        self.tier1_entry = ctk.CTkEntry(self.tiers_frame, width=100, placeholder_text="3")
        self.tier1_entry.pack(anchor="w")
        self.tier1_entry.insert(0, "3")

        ctk.CTkLabel(self.tiers_frame, text="Limite da Faixa 1 (R$):", font=ctk.CTkFont(size=11),
                      text_color=config.Colors.TEXT_SECONDARY).pack(anchor="w", pady=(5, 2))
        self.tier1_limit = ctk.CTkEntry(self.tiers_frame, width=100, placeholder_text="10000")
        self.tier1_limit.pack(anchor="w")

        ctk.CTkLabel(self.tiers_frame, text="Faixa 2 (% acima do limite):", font=ctk.CTkFont(size=11),
                      text_color=config.Colors.TEXT_SECONDARY).pack(anchor="w", pady=(5, 2))
        self.tier2_entry = ctk.CTkEntry(self.tiers_frame, width=100, placeholder_text="5")
        self.tier2_entry.pack(anchor="w")

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

        # Botão de Ação
        self.action_btn = self._create_action_button(content, "Calcular Comissões", self._run_calculation)

        # Progresso
        self.progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_frame.pack_forget()

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400, height=8)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        # Log
        self.log_text = ctk.CTkTextbox(content, height=80, font=ctk.CTkFont(size=10))
        self.log_text.pack(fill="x", padx=20, pady=5)
        self.log_text.insert("1.0", "Aguardando planilha...\n")
        self.log_text.configure(state="disabled")

        # Resultados
        self.results_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.results_frame.pack_forget()

        # Viewer
        self.viewer_btn = ResultViewerButton(
            self, content,
            lambda: self._last_result_text if hasattr(self, '_last_result_text') else "",
            "👁️ Visualizar Relatório Completo"
        )
        self.viewer_btn.pack(pady=(0, 15))

    def _toggle_rule_type(self):
        if self.rule_type_var.get() == "percentage":
            self.percentage_frame.pack(fill="x", padx=20, pady=(0, 15))
            self.tiers_frame.pack_forget()
        else:
            self.percentage_frame.pack_forget()
            self.tiers_frame.pack(fill="x", padx=20, pady=(0, 15))

    def _select_file(self, files=None):
        if files:
            self.sales_file = files[0]
            self.file_label.configure(text=f"✓ {os.path.basename(self.sales_file)}")
        else:
            files = self._browse_files([
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv")
            ])
            if files:
                self.sales_file = files[0]
                self.file_label.configure(text=f"✓ {os.path.basename(self.sales_file)}")

    def _run_calculation(self):
        if not self.sales_file:
            messagebox.showwarning("Aviso", "Selecione a planilha de vendas")
            return

        task_id, error = self.task_helper.start_task({"file": self.sales_file})
        if error:
            messagebox.showwarning("Aviso", error)
            return

        try:
            rate = float(self.percentage_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Percentual inválido. Use um número (ex: 5)")
            self.task_helper.cancel()
            return

        rules = {
            "type": self.rule_type_var.get(),
            "default_rate": rate,
            "tiers": [],
            "product_exceptions": {}
        }

        if rules["type"] == "tiers":
            try:
                tier1_rate = float(self.tier1_entry.get().strip())
                tier1_limit = float(self.tier1_limit.get().strip()) if self.tier1_limit.get().strip() else 0
                tier2_rate = float(self.tier2_entry.get().strip()) if self.tier2_entry.get().strip() else rate

                rules["tiers"] = [
                    {"min": 0, "max": tier1_limit, "rate": tier1_rate},
                    {"min": tier1_limit, "max": float('inf'), "rate": tier2_rate}
                ]
            except ValueError:
                messagebox.showerror("Erro", "Valores de taxa inválidos")
                self.task_helper.cancel()
                return

        if not self.start_execution():
            self.task_helper.cancel()
            return

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))

        sales_file = self.sales_file
        comissoes = self.comissoes
        global_executor.submit(
            execute_func=lambda: comissoes.calculate_commissions(sales_file, rules),
            on_complete=lambda result: self.after(0, lambda: self._on_calculation_done(result)),
            tool_name="comissoes",
            tool_display_name="Comissões",
            user_id=self.user_id
        )

    def _on_calculation_done(self, result):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")

        if result.get("success"):
            self.result_df = result.get("dataframe")
            self.ranking = result.get("ranking", [])
            self._show_results(result)

            rows = result.get("total_vendas", 0)
            self._finalize_execution(result, "", rows,
                                     {"vendas": rows, "comissoes": result.get('total_comissao', 0)})
        else:
            self._finalize_execution(result, "")
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

    def _show_results(self, result):
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for widget in self.results_frame.winfo_children():
            widget.destroy()

        summary_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        summary_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            summary_frame, text="📊 RESUMO EXECUTIVO",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w")

        metrics = [
            f"Total de Vendas: {result.get('total_vendas', 0)}",
            f"Vendedores: {result.get('total_vendedores', 0)}",
            f"Receita Total: R$ {result.get('total_receita', 0):,.2f}",
            f"Ticket Médio: R$ {result.get('ticket_medio', 0):,.2f}",
        ]
        for m in metrics:
            ctk.CTkLabel(summary_frame, text=m, font=ctk.CTkFont(size=12),
                          text_color=config.Colors.TEXT_SECONDARY).pack(anchor="w", pady=2)

        ctk.CTkLabel(
            summary_frame,
            text=f"💰 Total em Comissões: R$ {result.get('total_comissao', 0):,.2f}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.PRIMARY
        ).pack(anchor="w", pady=(10, 15))

        # Ranking
        if self.ranking:
            ctk.CTkLabel(
                summary_frame, text="🏆 RANKING DE PERFORMANCE",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY
            ).pack(anchor="w", pady=(10, 10))

            for r in self.ranking[:10]:
                row = ctk.CTkFrame(summary_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(row, text=r.get("medal", ""), width=30,
                              font=ctk.CTkFont(size=12)).pack(side="left")
                ctk.CTkLabel(row, text=r['vendedor'][:25], font=ctk.CTkFont(size=11),
                              text_color=config.Colors.TEXT_PRIMARY).pack(side="left", padx=(5, 10))
                ctk.CTkLabel(row, text=f"{r['vendas']} vendas", font=ctk.CTkFont(size=11),
                              text_color=config.Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 10))
                ctk.CTkLabel(row, text=f"R$ {r['comissao']:,.2f}", font=ctk.CTkFont(size=11, weight="bold"),
                              text_color=config.Colors.PRIMARY).pack(side="right")

        # Botões de ação
        btn_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(
            btn_frame, text="📄 Gerar PDFs por Vendedor",
            command=self._generate_pdfs,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="📊 Exportar Resumo Excel",
            command=self._export_summary,
            fg_color="transparent", border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(side="left")

        # Build report text for viewer
        report = f"📊 RELATÓRIO DE COMISSÕES\n{'='*45}\n"
        report += f"Vendas: {result.get('total_vendas')}\n"
        report += f"Receita: R$ {result.get('total_receita', 0):,.2f}\n"
        report += f"Comissões: R$ {result.get('total_comissao', 0):,.2f}\n\n"
        report += f"🏆 RANKING:\n"
        for r in self.ranking:
            report += f"{r['medal']} {r['vendedor']}: {r['vendas']} vendas | R$ {r['comissao']:,.2f}\n"

        self._last_result_text = report

    def _generate_pdfs(self):
        if self.result_df is None:
            return

        output_dir = self._browse_folder()
        if not output_dir:
            return

        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))

        result_df = self.result_df
        comissoes = self.comissoes
        global_executor.submit(
            execute_func=lambda: comissoes.generate_pdf_reports(result_df, output_dir, company_name="Empresa"),
            on_complete=lambda result: self.after(0, lambda: self._on_pdfs_done(result, output_dir)),
            tool_name="comissoes",
            tool_display_name="Comissões",
            user_id=self.user_id
        )

    def _on_pdfs_done(self, result, output_dir):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.progress_frame.pack_forget()
        if result.get("success"):
            messagebox.showinfo("Sucesso", f"✅ {result.get('total')} PDFs gerados em:\n{output_dir}")
        else:
            messagebox.showerror("Erro", result.get("error", "Erro ao gerar PDFs"))

    def _export_summary(self):
        if self.result_df is None:
            return

        theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
        visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

        output_path = self._create_output_path("resumo_comissoes.xlsx")
        if output_path:
            result = self.comissoes.export_summary(self.result_df, output_path, visual_theme=visual_theme)
            if result.get("success"):
                messagebox.showinfo("Sucesso", f"Resumo exportado para:\n{output_path}")
            else:
                messagebox.showerror("Erro", result.get("error"))

    def _show_error(self, error):
        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Falha no cálculo: {error}")
        self.execution.fail(error)
        self.task_helper.fail(error)

    def _create_output_path(self, default_name: str) -> str:
        from tkinter import filedialog
        return filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
        )

    def _browse_folder(self):
        from tkinter import filedialog
        return filedialog.askdirectory(title="Selecionar pasta para salvar PDFs")