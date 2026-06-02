"""
Calculadora de Preço por Canal de Venda — GUI Page
Interface para calcular preços por marketplace (ML, Shopee, Amazon, Magalu)
garantindo a margem líquida desejada.
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
from src.tools.precificador_canal.precificador_canal_v1 import PrecificadorCanal
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


class PrecificadorCanalPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.execution = ExecutionHelper("precificador_canal", "Calculadora de Preço por Canal", user_id)
        self._planilha_path = None
        self._last_output_path = None
        super().__init__(master, "precificador_canal", "Calculadora de Preço por Canal", on_back, execution_tracker, user_id)
        self.precificador = PrecificadorCanal(
            log_callback=self._log_from_thread,
            progress_callback=self._update_progress,
        )
        self._check_task_state()

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("precificador_canal")
        if not last_task:
            return
        status = last_task.get("status")
        if status == "completed":
            rows = last_task.get("rows_processed", 0)
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"✅ Última execução: {rows} produto(s) precificado(s)")

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
                    self.progress_label.configure(text=f"Calculando... {value}%")
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
                "Descubra o preço de venda ideal para cada marketplace e garanta sua margem líquida.\n"
                "Funciona com planilha em lote ou cálculo manual de produto único."
            ),
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=25, pady=(15, 5))

        # ── Abas: Planilha / Manual ────────────────────────────────────
        self.tab_view = ctk.CTkTabview(
            content,
            fg_color=config.Colors.CARD,
            segmented_button_fg_color=config.Colors.BORDER,
            segmented_button_selected_color=config.Colors.PRIMARY,
            segmented_button_selected_hover_color=config.Colors.PRIMARY_HOVER,
            segmented_button_unselected_color=config.Colors.BORDER,
            segmented_button_unselected_hover_color=config.Colors.CARD,
            corner_radius=12,
            height=300,
        )
        self.tab_view.pack(fill="x", padx=25, pady=10)
        self.tab_view.add("📊 Planilha em Lote")
        self.tab_view.add("✏️ Produto Único")

        self._build_tab_planilha(self.tab_view.tab("📊 Planilha em Lote"))
        self._build_tab_manual(self.tab_view.tab("✏️ Produto Único"))

        # ── Configurações de Margem e Canais ───────────────────────────
        self._build_config_section(content)

        # ── Botão de Ação ──────────────────────────────────────────────
        self.action_btn = self._create_action_button(content, "⚡ Calcular Preços", self._run)

        # ── Barra de Progresso ─────────────────────────────────────────
        self.progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=25, pady=(0, 5))
        self.progress_frame.pack_forget()

        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="", font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
        )
        self.progress_label.pack()
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=8)
        self.progress_bar.pack(fill="x", pady=4)
        self.progress_bar.set(0)

        # ── Log de execução ────────────────────────────────────────────
        log_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        log_frame.pack(fill="both", expand=True, padx=25, pady=10)

        ctk.CTkLabel(
            log_frame, text="Log de Execução:",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=15, pady=(12, 4))

        self.log_text = ctk.CTkTextbox(log_frame, height=160, font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 12))
        self.log_text.insert("1.0", "Aguardando execução...\n")
        self.log_text.configure(state="disabled")

        # ── Botão de exportação ────────────────────────────────────────
        self.export_btn = ctk.CTkButton(
            content,
            text="📂 Abrir Arquivo Gerado",
            state="disabled",
            width=220,
            height=38,
            fg_color=config.Colors.BORDER,
            hover_color=config.Colors.PRIMARY,
            text_color=config.Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            corner_radius=8,
            command=self._open_output,
        )
        self.export_btn.pack(pady=(0, 20))

    def _build_tab_planilha(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            parent,
            text="Planilha com colunas: Produto | Custo | Imposto_pct",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
        )
        info.pack(anchor="w", padx=10, pady=(8, 4))

        file_frame = ctk.CTkFrame(parent, fg_color=config.Colors.BORDER, corner_radius=8, height=70)
        file_frame.pack(fill="x", padx=10, pady=4)
        file_frame.pack_propagate(False)

        self.file_label = ctk.CTkLabel(
            file_frame,
            text="📁  Nenhuma planilha selecionada — clique para escolher ou arraste aqui",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
        )
        self.file_label.pack(expand=True)
        file_frame.bind("<Button-1>", lambda e: self._browse_file())
        self.file_label.bind("<Button-1>", lambda e: self._browse_file())

        ctk.CTkButton(
            parent,
            text="📂 Selecionar Planilha (.xlsx / .csv)",
            width=240, height=34,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._browse_file,
        ).pack(pady=(6, 10))

    def _build_tab_manual(self, parent):
        fields = [
            ("Produto / Descrição:", "produto_entry", "Ex: Fone de Ouvido Bluetooth"),
            ("Custo de Aquisição (R$):", "custo_entry", "Ex: 45.00"),
            ("Imposto Simples Nacional (%):", "imposto_entry", "Ex: 6.0"),
        ]
        for label, attr, placeholder in fields:
            ctk.CTkLabel(
                parent, text=label,
                font=ctk.CTkFont(size=12),
                text_color=config.Colors.TEXT_SECONDARY,
            ).pack(anchor="w", padx=15, pady=(10, 2))
            entry = ctk.CTkEntry(
                parent, width=320, placeholder_text=placeholder,
                font=ctk.CTkFont(size=12),
            )
            entry.pack(anchor="w", padx=15)
            setattr(self, attr, entry)

    def _build_config_section(self, parent):
        cfg_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        cfg_frame.pack(fill="x", padx=25, pady=8)
        cfg_frame.grid_columnconfigure((0, 1), weight=1)

        # Margem
        left = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        left.grid(row=0, column=0, padx=20, pady=15, sticky="ew")

        ctk.CTkLabel(
            left, text="🎯  Margem Líquida Desejada",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w")

        self.margem_label = ctk.CTkLabel(
            left, text="20%",
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"),
            text_color=config.Colors.PRIMARY,
        )
        self.margem_label.pack(anchor="w", pady=4)

        self.margem_slider = ctk.CTkSlider(
            left, from_=5, to=60, number_of_steps=55,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER,
            progress_color=config.Colors.PRIMARY,
            command=self._on_margem_change,
        )
        self.margem_slider.set(20)
        self.margem_slider.pack(fill="x", pady=4)

        ctk.CTkLabel(
            left, text="5%                    60%",
            font=ctk.CTkFont(size=10),
            text_color=config.Colors.TEXT_SECONDARY,
        ).pack(anchor="w")

        # Canais
        right = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        right.grid(row=0, column=1, padx=20, pady=15, sticky="new")

        ctk.CTkLabel(
            right, text="🛒  Canais de Venda",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        self._canal_vars = {}
        canais_config = [
            ("Mercado Livre", True),
            ("Shopee", True),
            ("Amazon", True),
            ("Magalu", False),
        ]
        for nome, default in canais_config:
            var = ctk.BooleanVar(value=default)
            self._canal_vars[nome] = var
            ctk.CTkCheckBox(
                right, text=nome, variable=var,
                checkbox_width=18, checkbox_height=18,
                checkmark_color="white",
                fg_color=config.Colors.PRIMARY,
                hover_color=config.Colors.PRIMARY_HOVER,
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", pady=2)

    def _on_margem_change(self, value):
        self.margem_label.configure(text=f"{int(value)}%")

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar planilha de produtos",
            filetypes=[("Planilhas", "*.xlsx *.xls *.csv"), ("Todos", "*.*")],
        )
        if path:
            self._planilha_path = path
            nome = os.path.basename(path)
            self.file_label.configure(
                text=f"✅  {nome}",
                text_color=config.Colors.PRIMARY,
            )

    def _run(self):
        tab = self.tab_view.get()
        margem = self.margem_slider.get()
        canais = [k for k, v in self._canal_vars.items() if v.get()]

        if not canais:
            messagebox.showwarning("Aviso", "Selecione pelo menos um canal de venda.")
            return

        if "Planilha" in tab:
            if not self._planilha_path:
                messagebox.showwarning("Aviso", "Selecione uma planilha de produtos.")
                return
            self._run_planilha(margem, canais)
        else:
            self._run_manual(margem, canais)

    def _run_planilha(self, margem, canais):
        try:
            ext = os.path.splitext(self._planilha_path)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(self._planilha_path, sep=None, engine="python")
            else:
                df = pd.read_excel(self._planilha_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler planilha:\n{e}")
            return
        self._execute(df, margem, canais)

    def _run_manual(self, margem, canais):
        produto = self.produto_entry.get().strip() or "Produto"
        custo_str = self.custo_entry.get().strip().replace(",", ".")
        imposto_str = self.imposto_entry.get().strip().replace(",", ".") or "6.0"
        if not custo_str:
            messagebox.showwarning("Aviso", "Informe o custo de aquisição.")
            return
        try:
            custo = float(custo_str)
            imposto = float(imposto_str)
        except ValueError:
            messagebox.showerror("Erro", "Custo ou imposto com formato inválido.")
            return
        df = pd.DataFrame([{"produto": produto, "custo": custo, "imposto_pct": imposto}])
        self._execute(df, margem, canais)

    def _execute(self, df, margem, canais):
        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=25, pady=(0, 5))
        self.progress_bar.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.export_btn.configure(state="disabled", fg_color=config.Colors.BORDER)

        precificador = self.precificador

        def execute_func():
            return precificador.calcular_planilha(df, margem, canais)

        def on_complete(result):
            self.after(0, lambda: self._show_result(result))

        task_executor.submit(
            execute_func=execute_func,
            on_complete=on_complete,
            tool_name="precificador_canal",
            tool_display_name="Calculadora de Preço por Canal",
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
            messagebox.showerror("Erro", f"Falha no cálculo:\n{result.get('error', 'Erro desconhecido')}")
            self._finalize_execution(result, "")
            return

        rows = result.get("rows", 0)
        output = result.get("output_path", "")
        self._last_output_path = output

        self.export_btn.configure(
            state="normal",
            fg_color=config.Colors.PRIMARY,
        )

        self._add_log(f"✅ {rows} produto(s) precificado(s) com sucesso!")
        self._add_log(f"📂 Arquivo: {os.path.basename(output)}")

        messagebox.showinfo(
            "Sucesso!",
            f"Precificação concluída!\n\n{rows} produto(s) calculado(s).\nArquivo salvo em:\n{output}",
        )
        self._finalize_execution(result, output, rows, {"produtos": rows})

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
                    tool_name="precificador_canal",
                    rows_processed=rows,
                    user_id=self.user_id,
                )
            except Exception:
                pass
