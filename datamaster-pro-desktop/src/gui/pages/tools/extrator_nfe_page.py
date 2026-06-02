"""
Extrator NF-e / XML + Conciliador de Pedidos — GUI Page
Cruza XMLs de Notas Fiscais com planilha de vendas do marketplace.
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.extrator_nfe.extrator_nfe_v1 import ExtratorNFe
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


class ExtratorNfePage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.extrator = ExtratorNFe(
            log_callback=self._log_from_thread,
            progress_callback=self._update_progress,
        )
        self.execution = ExecutionHelper("extrator_nfe", "Extrator NF-e / Conciliador", user_id)
        self._xml_path = None
        self._planilha_path = None
        self._last_output_path = None
        super().__init__(master, "extrator_nfe", "Extrator NF-e + Conciliador", on_back, execution_tracker, user_id)
        self._check_task_state()

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("extrator_nfe")
        if not last_task:
            return
        status = last_task.get("status")
        if status == "completed" and hasattr(self, "status_label"):
            rows = last_task.get("rows_processed", 0)
            self.status_label.configure(text=f"✅ Última execução: {rows} NF-e(s) processada(s)")

    def _log_from_thread(self, message: str):
        self.after(0, lambda: self._add_log(message))

    def _add_log(self, message: str):
        try:
            if hasattr(self, "log_text") and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", f"• {message}\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            pass

    def _update_progress(self, value: int):
        try:
            def _apply():
                if hasattr(self, "progress_bar") and self.progress_bar.winfo_exists():
                    self.progress_bar.set(value / 100)
                if hasattr(self, "progress_label") and self.progress_label.winfo_exists():
                    self.progress_label.configure(text=f"Processando... {value}%")
            self.after(0, _apply)
        except Exception:
            pass

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        # ── Descrição ─────────────────────────────────────────────────
        ctk.CTkLabel(
            content,
            text=(
                "Cruza automaticamente os XMLs de Notas Fiscais com a planilha de vendas do marketplace.\n"
                "Detecta: pedidos sem nota, valores divergentes e notas sem pedido."
            ),
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=25, pady=(15, 10))

        # ── Painel de entradas ─────────────────────────────────────────
        inputs_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        inputs_frame.pack(fill="x", padx=25, pady=8)
        inputs_frame.grid_columnconfigure((0, 1), weight=1)

        # Coluna esquerda: XMLs
        left = ctk.CTkFrame(inputs_frame, fg_color="transparent")
        left.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(
            left,
            text="📂  Pasta de XMLs das NF-e",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            left,
            text="Selecione a pasta onde o sistema emissor\nsalva os arquivos .XML das Notas Fiscais.",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        self.xml_label = ctk.CTkLabel(
            left,
            text="Nenhuma pasta selecionada",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
        )
        self.xml_label.pack(anchor="w", pady=(0, 6))

        btn_xml_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_xml_frame.pack(anchor="w")

        ctk.CTkButton(
            btn_xml_frame,
            text="📁 Selecionar Pasta de XMLs",
            width=210, height=34,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._browse_xml_folder,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_xml_frame,
            text="📄 Arquivo único",
            width=120, height=34,
            fg_color=config.Colors.BORDER,
            hover_color=config.Colors.PRIMARY,
            text_color=config.Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            command=self._browse_xml_file,
        ).pack(side="left")

        # Separador vertical
        sep = ctk.CTkFrame(inputs_frame, width=1, fg_color=config.Colors.BORDER)
        sep.grid(row=0, column=1, sticky="ns", padx=0, pady=20)

        # Coluna direita: Planilha
        right = ctk.CTkFrame(inputs_frame, fg_color="transparent")
        right.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")
        inputs_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            right,
            text="📊  Planilha de Vendas do Marketplace",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            right,
            text="Exportação do Mercado Livre, Shopee ou\nqualquer planilha com Pedido/CPF e Valor.",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        self.planilha_label = ctk.CTkLabel(
            right,
            text="Nenhuma planilha selecionada",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
        )
        self.planilha_label.pack(anchor="w", pady=(0, 6))

        ctk.CTkButton(
            right,
            text="📊 Selecionar Planilha (.xlsx / .csv)",
            width=240, height=34,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._browse_planilha,
        ).pack(anchor="w")

        # ── Configurações de cruzamento ────────────────────────────────
        cfg_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        cfg_frame.pack(fill="x", padx=25, pady=8)
        cfg_frame.grid_columnconfigure((0, 1), weight=1)

        left_cfg = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        left_cfg.grid(row=0, column=0, padx=20, pady=15, sticky="ew")

        ctk.CTkLabel(
            left_cfg,
            text="🔑  Chave de Cruzamento",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        self.chave_var = ctk.StringVar(value="auto")
        opcoes = [
            ("auto", "🤖 Automático (recomendado)"),
            ("numero_pedido", "🔢 Número do Pedido"),
            ("cpf_cnpj", "👤 CPF / CNPJ do Comprador"),
        ]
        for val, texto in opcoes:
            ctk.CTkRadioButton(
                left_cfg,
                text=texto,
                variable=self.chave_var,
                value=val,
                font=ctk.CTkFont(size=12),
                fg_color=config.Colors.PRIMARY,
                hover_color=config.Colors.PRIMARY_HOVER,
            ).pack(anchor="w", pady=3)

        right_cfg = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        right_cfg.grid(row=0, column=1, padx=20, pady=15, sticky="ew")

        ctk.CTkLabel(
            right_cfg,
            text="⚙️  Tolerância de Valor",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        self.tolerancia_label = ctk.CTkLabel(
            right_cfg,
            text="R$ 0,01",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=config.Colors.PRIMARY,
        )
        self.tolerancia_label.pack(anchor="w", pady=4)

        self.tolerancia_slider = ctk.CTkSlider(
            right_cfg, from_=0.01, to=5.0,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER,
            progress_color=config.Colors.PRIMARY,
            command=self._on_tolerancia_change,
        )
        self.tolerancia_slider.set(0.01)
        self.tolerancia_slider.pack(fill="x", pady=4)

        ctk.CTkLabel(
            right_cfg,
            text="R$ 0,01                    R$ 5,00",
            font=ctk.CTkFont(size=10),
            text_color=config.Colors.TEXT_SECONDARY,
        ).pack(anchor="w")

        # ── Botão de ação ──────────────────────────────────────────────
        self.action_btn = self._create_action_button(content, "🔍 Cruzar Pedidos com NF-e", self._run)

        # ── Progresso ─────────────────────────────────────────────────
        self.progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=25, pady=(0, 5))
        self.progress_frame.pack_forget()

        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="",
            font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY,
        )
        self.progress_label.pack()
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=8)
        self.progress_bar.pack(fill="x", pady=4)
        self.progress_bar.set(0)

        # ── Painel de resultados ───────────────────────────────────────
        res_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        res_frame.pack(fill="x", padx=25, pady=8)
        res_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._result_cards = {}
        cards_config = [
            ("ok", "✅ OK", "10B981"),
            ("divergentes", "⚠️ Divergentes", "F59E0B"),
            ("faltando", "❌ Faltando", "EF4444"),
            ("sem_nota", "📋 Sem Nota", "8B5CF6"),
        ]
        for i, (key, label, color) in enumerate(cards_config):
            card = ctk.CTkFrame(res_frame, fg_color="transparent")
            card.grid(row=0, column=i, padx=15, pady=15, sticky="ew")
            num = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(family="Inter", size=32, weight="bold"),
                text_color=f"#{color}",
            )
            num.pack()
            ctk.CTkLabel(
                card, text=label,
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=config.Colors.TEXT_SECONDARY,
            ).pack()
            self._result_cards[key] = num

        # ── Log ───────────────────────────────────────────────────────
        log_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        log_frame.pack(fill="both", expand=True, padx=25, pady=8)

        ctk.CTkLabel(
            log_frame, text="Log de Processamento:",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=15, pady=(12, 4))

        self.log_text = ctk.CTkTextbox(log_frame, height=150, font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 12))
        self.log_text.insert("1.0", "Aguardando execução...\n")
        self.log_text.configure(state="disabled")

        # ── Exportação ────────────────────────────────────────────────
        self.export_btn = ctk.CTkButton(
            content,
            text="📂 Abrir Relatório Gerado",
            state="disabled",
            width=220, height=38,
            fg_color=config.Colors.BORDER,
            hover_color=config.Colors.PRIMARY,
            text_color=config.Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            corner_radius=8,
            command=self._open_output,
        )
        self.export_btn.pack(pady=(0, 20))

    def _on_tolerancia_change(self, value):
        self.tolerancia_label.configure(text=f"R$ {value:.2f}")

    def _browse_xml_folder(self):
        path = filedialog.askdirectory(title="Selecionar pasta de XMLs")
        if path:
            self._xml_path = path
            n = len([f for f in os.listdir(path) if f.lower().endswith(".xml")])
            self.xml_label.configure(
                text=f"✅  {os.path.basename(path)}  ({n} XML(s))",
                text_color=config.Colors.PRIMARY,
            )

    def _browse_xml_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar XML de NF-e",
            filetypes=[("XML", "*.xml"), ("Todos", "*.*")],
        )
        if path:
            self._xml_path = path
            self.xml_label.configure(
                text=f"✅  {os.path.basename(path)}",
                text_color=config.Colors.PRIMARY,
            )

    def _browse_planilha(self):
        path = filedialog.askopenfilename(
            title="Selecionar planilha de vendas",
            filetypes=[("Planilhas", "*.xlsx *.xls *.csv"), ("Todos", "*.*")],
        )
        if path:
            self._planilha_path = path
            self.planilha_label.configure(
                text=f"✅  {os.path.basename(path)}",
                text_color=config.Colors.PRIMARY,
            )

    def _run(self):
        if not self._xml_path:
            messagebox.showwarning("Aviso", "Selecione a pasta ou arquivo de XMLs.")
            return
        if not self._planilha_path:
            messagebox.showwarning("Aviso", "Selecione a planilha de vendas do marketplace.")
            return

        chave = self.chave_var.get()
        tolerancia = self.tolerancia_slider.get()

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=25, pady=(0, 5))
        self.progress_bar.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.export_btn.configure(state="disabled", fg_color=config.Colors.BORDER)

        for card in self._result_cards.values():
            card.configure(text="—")

        extrator = self.extrator
        xml_path = self._xml_path
        planilha_path = self._planilha_path

        def execute_func():
            return extrator.cruzar_com_planilha(xml_path, planilha_path, chave, tolerancia)

        def on_complete(result):
            self.after(0, lambda: self._show_result(result))

        task_executor.submit(
            execute_func=execute_func,
            on_complete=on_complete,
            tool_name="extrator_nfe",
            tool_display_name="Extrator NF-e / Conciliador",
            user_id=self.user_id,
        )

    def _show_result(self, result):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self.progress_frame.pack_forget()
        self.action_btn.configure(state="normal")

        if not result.get("success"):
            messagebox.showerror("Erro", f"Falha no cruzamento:\n{result.get('error', 'Erro desconhecido')}")
            self._finalize_execution(result, "")
            return

        ok = result.get("ok", 0)
        div = result.get("divergentes", 0)
        fat = result.get("faltando", 0)
        sem = result.get("sem_nota", 0)
        output = result.get("output_path", "")
        self._last_output_path = output

        self._result_cards["ok"].configure(text=str(ok))
        self._result_cards["divergentes"].configure(text=str(div))
        self._result_cards["faltando"].configure(text=str(fat))
        self._result_cards["sem_nota"].configure(text=str(sem))

        self.export_btn.configure(state="normal", fg_color=config.Colors.PRIMARY)

        total = ok + div + fat + sem
        self._finalize_execution(result, output, total, {"ok": ok, "divergentes": div})

        msg = (
            f"Cruzamento concluído!\n\n"
            f"✅ Conciliados: {ok}\n"
            f"⚠️ Divergentes: {div}\n"
            f"❌ Faltando: {fat}\n"
            f"📋 Pedidos s/ Nota: {sem}\n\n"
            f"Relatório salvo em:\n{os.path.basename(output)}"
        )
        messagebox.showinfo("Concluído!", msg)

    def _open_output(self):
        if self._last_output_path and os.path.exists(self._last_output_path):
            os.startfile(self._last_output_path)

    def _finalize_execution(self, result, output_path, rows=0, extra=None):
        if hasattr(self, "execution"):
            try:
                self.execution.finalize(result, output_path, rows, extra or {})
            except Exception:
                pass
        if hasattr(self, "execution_tracker") and self.execution_tracker and rows > 0:
            try:
                self.execution_tracker.record_execution(
                    tool_name="extrator_nfe",
                    rows_processed=rows,
                    user_id=self.user_id,
                )
            except Exception:
                pass
