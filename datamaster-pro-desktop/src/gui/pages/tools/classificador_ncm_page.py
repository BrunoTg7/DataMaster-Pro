"""
Classificador NCM/CEST Enterprise — GUI Page
Base oficial TIPI (Receita Federal) + CEST (Convênio ICMS 92/2015)
Pipeline ETL automatizado + Fuzzy matching hierárquico + Auditoria completa
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.classificador_ncm import ClassificadorNCMEntperprise, NCMPipeline
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor
import json


class ClassificadorNcmPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self._tk_ready = False
        self._db_ready = False
        self._check_database()
        
        # Usar classificador enterprise
        self.classificador = ClassificadorNCMEntperprise(
            log_callback=self._log_safe,
            progress_callback=self._update_progress,
        )
        self.execution = ExecutionHelper("classificador_ncm", "Classificador NCM/CEST Enterprise", user_id)
        self._planilha_path = None
        self._last_output_path = None
        super().__init__(master, "classificador_ncm", "Classificador NCM/CEST Enterprise", on_back, execution_tracker, user_id)
        self._tk_ready = True
        self._check_task_state()

    def _check_database(self):
        """Verifica se a base NCM/CEST existe e oferece para gerar se não existir"""
        db_path = os.path.join("data", "processed", "ncm_database.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._db_ready = True
                self._log_safe(f"✅ Base NCM/CEST carregada: {len(data)} registros")
            except Exception as e:
                self._log_safe(f"⚠️ Erro ao ler base NCM: {e}")
                self._db_ready = False
        else:
            self._db_ready = False
            self._log_safe("⚠️ Base NCM/CEST NÃO ENCONTRADA. Execute 'Atualizar Base NCM' para gerar.")

    def _log_safe(self, message: str):
        if not self._tk_ready:
            print(f"[LOG] {message}")
            return
        if "Erro" not in message and "ERRO" not in message:
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

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("classificador_ncm")
        if not last_task:
            return
        status = last_task.get("status")
        if status == "completed" and hasattr(self, "status_label"):
            rows = last_task.get("rows_processed", 0)
            self.status_label.configure(text=f"✅ Última execução: {rows} produto(s) classificado(s)")

    def _update_progress(self, value: int):
        try:
            def _apply():
                if hasattr(self, "progress_bar") and self.progress_bar.winfo_exists():
                    self.progress_bar.set(value / 100)
                if hasattr(self, "progress_label") and self.progress_label.winfo_exists():
                    self.progress_label.configure(text=f"Classificando... {value}%")
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
                "Classifique automaticamente seus produtos com os códigos NCM e CEST corretos.\n"
                "Envie uma planilha com as descrições e receba as sugestões em segundos."
            ),
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=25, pady=(15, 5))

        # ── Painel informativo ─────────────────────────────────────────
        info_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        info_frame.pack(fill="x", padx=25, pady=8)
        info_frame.grid_columnconfigure((0, 1, 2), weight=1)

        items_info = [
            ("🏷️", "NCM", "Nomenclatura Comum\ndo Mercosul"),
            ("🔖", "CEST", "Código Especificador da\nSubstituição Tributária"),
            (f"📦", f"{len(self.classificador._descricoes)}", "Categorias no\nbanco de dados"),
        ]
        for i, (icon, val, lbl) in enumerate(items_info):
            card = ctk.CTkFrame(info_frame, fg_color="transparent")
            card.grid(row=0, column=i, padx=15, pady=15, sticky="ew")
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack()
            ctk.CTkLabel(
                card, text=val,
                font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
                text_color=config.Colors.PRIMARY,
            ).pack()
            ctk.CTkLabel(
                card, text=lbl,
                font=ctk.CTkFont(size=10),
                text_color=config.Colors.TEXT_SECONDARY,
                justify="center",
            ).pack()

        # ── Upload de planilha ─────────────────────────────────────────
        upload_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        upload_frame.pack(fill="x", padx=25, pady=8)

        ctk.CTkLabel(
            upload_frame,
            text="📊  Planilha de Produtos",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            upload_frame,
            text=(
                "A planilha deve ter uma coluna com as descrições dos produtos.\n"
                "Nomes aceitos: Produto, Descrição, Nome, Item, Description, Título."
            ),
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 10))

        drop_zone = ctk.CTkFrame(
            upload_frame,
            fg_color=config.Colors.BORDER,
            corner_radius=8,
            height=80,
        )
        drop_zone.pack(fill="x", padx=20, pady=(0, 10))
        drop_zone.pack_propagate(False)

        self.file_label = ctk.CTkLabel(
            drop_zone,
            text="📁  Nenhuma planilha selecionada — clique para escolher",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
        )
        self.file_label.pack(expand=True)
        drop_zone.bind("<Button-1>", lambda e: self._browse_file())
        self.file_label.bind("<Button-1>", lambda e: self._browse_file())

        ctk.CTkButton(
            upload_frame,
            text="📂 Selecionar Planilha (.xlsx / .csv)",
            width=240, height=34,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._browse_file,
        ).pack(pady=(0, 15))

        # ── Modo de entrada manual ────────────────────────────────────
        manual_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        manual_frame.pack(fill="x", padx=25, pady=8)

        ctk.CTkLabel(
            manual_frame,
            text="✏️  Classificação Rápida (Produto Único)",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(15, 8))

        input_row = ctk.CTkFrame(manual_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=20, pady=(0, 15))

        self.manual_entry = ctk.CTkEntry(
            input_row,
            width=400,
            placeholder_text="Ex: Fone de Ouvido Bluetooth sem fio",
            font=ctk.CTkFont(size=12),
        )
        self.manual_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            input_row,
            text="Classificar →",
            width=130, height=35,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._classify_single,
        ).pack(side="left")

        # Resultado rápido
        self.quick_result_frame = ctk.CTkFrame(manual_frame, fg_color=config.Colors.BORDER, corner_radius=8)
        self.quick_result_frame.pack(fill="x", padx=20, pady=(0, 15))
        self.quick_result_frame.pack_forget()

        self.quick_result_label = ctk.CTkLabel(
            self.quick_result_frame,
            text="",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=config.Colors.TEXT_PRIMARY,
            justify="left",
        )
        self.quick_result_label.pack(padx=15, pady=10)

        # ── Botão principal ────────────────────────────────────────────
        self.action_btn = self._create_action_button(content, "🏷️ Classificar Planilha Completa", self._run_planilha)

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

        # ── Cards de resultado ─────────────────────────────────────────
        res_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        res_frame.pack(fill="x", padx=25, pady=8)
        res_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._result_cards = {}
        cards_config = [
            ("classificados", "✅ Classificados", "10B981"),
            ("verificar", "⚠️ Verificar", "F59E0B"),
            ("revisao", "🔴 Revisão Manual", "EF4444"),
        ]
        for i, (key, lbl, color) in enumerate(cards_config):
            card = ctk.CTkFrame(res_frame, fg_color="transparent")
            card.grid(row=0, column=i, padx=15, pady=15, sticky="ew")
            num = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(family="Inter", size=32, weight="bold"),
                text_color=f"#{color}",
            )
            num.pack()
            ctk.CTkLabel(
                card, text=lbl,
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

        self.log_text = ctk.CTkTextbox(log_frame, height=140, font=ctk.CTkFont(size=11))
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

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar planilha de produtos",
            filetypes=[("Planilhas", "*.xlsx *.xls *.csv"), ("Todos", "*.*")],
        )
        if path:
            self._planilha_path = path
            self.file_label.configure(
                text=f"✅  {os.path.basename(path)}",
                text_color=config.Colors.PRIMARY,
            )

    def _classify_single(self):
        """Classificação rápida de um produto único."""
        desc = self.manual_entry.get().strip()
        if not desc:
            messagebox.showwarning("Aviso", "Digite a descrição do produto.")
            return

        resultado = self.classificador._classificar_um(desc)
        ncm = resultado.get("ncm", "—") or "—"
        cest = resultado.get("cest", "—") or "—"
        tipi = resultado.get("descricao_tipi", "—") or "—"
        conf = resultado.get("confianca_pct", 0)
        status = resultado.get("status", "")

        text = (
            f"{status}\n"
            f"NCM: {ncm}   |   CEST: {cest}   |   Confiança: {conf}%\n"
            f"Classificação TIPI: {tipi}"
        )
        self.quick_result_label.configure(text=text)
        self.quick_result_frame.pack(fill="x", padx=20, pady=(0, 15))

    def _run_planilha(self):
        if not self._planilha_path:
            messagebox.showwarning("Aviso", "Selecione uma planilha de produtos.")
            return

        try:
            ext = os.path.splitext(self._planilha_path)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(self._planilha_path, sep=None, engine="python", dtype=str)
            else:
                df = pd.read_excel(self._planilha_path, dtype=str)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler planilha:\n{e}")
            return

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=25, pady=(0, 5))
        self.progress_bar.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.export_btn.configure(state="disabled", fg_color=config.Colors.BORDER)

        for card in self._result_cards.values():
            card.configure(text="—")

        classificador = self.classificador

        def execute_func():
            return classificador.classificar_planilha(df)

        def on_complete(result):
            self.after(0, lambda: self._show_result(result))

        task_executor.submit(
            execute_func=execute_func,
            on_complete=on_complete,
            tool_name="classificador_ncm",
            tool_display_name="Classificador NCM/CEST",
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
            messagebox.showerror("Erro", f"Falha na classificação:\n{result.get('error', 'Erro desconhecido')}")
            self._finalize_execution(result, "")
            return

        classif = result.get("classificados", 0)
        verif = result.get("verificar", 0)
        rev = result.get("revisao_manual", 0)
        total = result.get("rows", 0)
        output = result.get("output_path", "")
        self._last_output_path = output

        self._result_cards["classificados"].configure(text=str(classif))
        self._result_cards["verificar"].configure(text=str(verif))
        self._result_cards["revisao"].configure(text=str(rev))

        self.export_btn.configure(state="normal", fg_color=config.Colors.PRIMARY)
        self._finalize_execution(result, output, total, {"classificados": classif, "revisao": rev})

        msg = (
            f"Classificação concluída!\n\n"
            f"✅ Classificados: {classif}\n"
            f"⚠️ Para verificar: {verif}\n"
            f"🔴 Revisão manual: {rev}\n\n"
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
                    tool_name="classificador_ncm",
                    rows_processed=rows,
                    user_id=self.user_id,
                )
            except Exception:
                pass
