import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.conciliador.conciliador_v2 import Conciliador
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.global_executor import global_executor


class ConciliadorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.conciliador = Conciliador(log_callback=self._log_msg)
        self.task_helper = TaskHelper("conciliador")
        self.execution = ExecutionHelper("conciliador", "Conciliador Pro", user_id)
        self._task_id = None
        self.extract_file = ""
        self.sales_file = ""
        self.xml_folder = ""
        self.mode = "classic"
        super().__init__(master, "conciliador", "Conciliador Pro", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.log_messages = []

    def _check_task_state(self):
        from src.core.storage.storage_manager import StorageManager
        storage = StorageManager()
        last_task = storage.get_last_task_by_tool("conciliador")

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

    def _log_msg(self, msg: str):
        try:
            self.log_messages.append(msg)
        except Exception:
            pass

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        mode_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        mode_frame.pack(fill="x", padx=20, pady=(20, 10))

        mode_lbl = ctk.CTkLabel(
            mode_frame,
            text="Modo de Conciliação:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        mode_lbl.pack(anchor="w", padx=20, pady=(15, 10))

        self.mode_var = ctk.StringVar(value="classic")

        classic_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Clássico (Extrato ↔ Vendas)",
            variable=self.mode_var,
            value="classic",
            command=self._toggle_mode,
            font=ctk.CTkFont(size=12)
        )
        classic_radio.pack(anchor="w", padx=20, pady=2)

        nfe_radio = ctk.CTkRadioButton(
            mode_frame,
            text="NF-e (XML de Notas ↔ Extrato)",
            variable=self.mode_var,
            value="nfe",
            command=self._toggle_mode,
            font=ctk.CTkFont(size=12)
        )
        nfe_radio.pack(anchor="w", padx=20, pady=(0, 15))

        self.info_label = ctk.CTkLabel(
            content,
            text="Cruze extratos bancários com planilhas de vendas para encontrar divergências.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        self.info_label.pack(pady=(10, 10))

        self.file1_drop = self._create_drop_zone(
            content,
            "Selecione o primeiro arquivo",
            self._select_file1
        )
        self.file1_drop.pack(fill="x", padx=20, pady=10)

        self.file1_label = ctk.CTkLabel(
            content,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file1_label.pack(pady=(0, 5))

        self.file2_drop = self._create_drop_zone(
            content,
            "Selecione o segundo arquivo",
            self._select_file2
        )
        self.file2_drop.pack(fill="x", padx=20, pady=10)

        self.file2_label = ctk.CTkLabel(
            content,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file2_label.pack(pady=(0, 5))

        self.file3_drop = self._create_drop_zone(
            content,
            "Selecione pasta com XMLs (NF-e)",
            self._select_xml_folder
        )
        self.file3_drop.pack_forget()

        self.file3_label = ctk.CTkLabel(
            content,
            text="Nenhuma pasta selecionada",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file3_label.pack_forget()

        options_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        options_frame.pack(fill="x", padx=20, pady=10)

        # Linha: Tolerância + Tema lado a lado
        row = ctk.CTkFrame(options_frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(15, 15))

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(20, 0))

        ctk.CTkLabel(
            left,
            text="Tolerância de valor (R$):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 5))

        self.tolerance_entry = ctk.CTkEntry(
            left,
            width=100,
            placeholder_text="0.05"
        )
        self.tolerance_entry.insert(0, "0.05")
        self.tolerance_entry.pack(anchor="w")

        ctk.CTkLabel(
            right,
            text="Tema Visual da Planilha (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 5))

        self.visual_theme_menu = ctk.CTkOptionMenu(
            right,
            values=["Azul Corporativo", "Verde Esmeralda", "Laranja Moderno", "Cinza Minimalista"],
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER
        )
        self.visual_theme_menu.set("Azul Corporativo")
        self.visual_theme_menu.pack(anchor="w")

        self.action_btn = self._create_action_button(content, "Iniciar Conciliação", self._run_reconcile)

        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)

    def _toggle_mode(self):
        self.mode = self.mode_var.get()
        self._reset_files()

        if self.mode == "nfe":
            self.info_label.configure(text="Cruze XMLs de Notas Fiscais (NF-e) com o extrato bancário para ver quais notas foram pagas.")
            if hasattr(self, 'drop_label'):
                self.drop_label.configure(text="1. Selecione o Extrato Bancário")
            if hasattr(self, 'drop_sublabel'):
                self.drop_sublabel.configure(text="2. Selecione a Pasta com XMLs")
            self.file3_drop.pack_forget()
            self.file3_label.pack_forget()
        else:
            self.info_label.configure(text="Cruze extratos bancários (OFX/CSV/XLSX) com planilhas de vendas para encontrar divergências.")
            if hasattr(self, 'drop_label'):
                self.drop_label.configure(text="1. Selecione o Extrato Bancário")
            if hasattr(self, 'drop_sublabel'):
                self.drop_sublabel.configure(text="2. Selecione a Planilha de Vendas")
            self.file3_drop.pack_forget()
            self.file3_label.pack_forget()

    def _reset_files(self):
        self.extract_file = ""
        self.sales_file = ""
        self.xml_folder = ""
        self.file1_label.configure(text="Nenhum arquivo selecionado")
        self.file2_label.configure(text="Nenhum arquivo selecionado")
        self.file3_label.configure(text="Nenhuma pasta selecionada")

    def _select_file1(self, files=None):
        if files:
            self.extract_file = files[0]
            self.file1_label.configure(text=f"✓ {os.path.basename(self.extract_file)}")
        else:
            if self.mode == "nfe":
                filetypes = [("OFX", "*.ofx"), ("Excel", "*.xlsx *.xls"), ("CSV", "*.csv"), ("Todos", "*.*")]
            else:
                filetypes = [("OFX", "*.ofx"), ("Excel", "*.xlsx *.xls"), ("CSV", "*.csv"), ("Todos", "*.*")]
            files = self._browse_files(filetypes)
            if files:
                self.extract_file = files[0]
                self.file1_label.configure(text=f"✓ {os.path.basename(self.extract_file)}")

    def _select_file2(self, files=None):
        if files:
            if self.mode == "nfe":
                self.xml_folder = files[0]
                self.file2_label.configure(text=f"✓ {os.path.basename(self.xml_folder)}")
            else:
                self.sales_file = files[0]
                self.file2_label.configure(text=f"✓ {os.path.basename(self.sales_file)}")
        else:
            if self.mode == "nfe":
                folder = self._browse_folder()
                if folder:
                    self.xml_folder = folder
                    self.file2_label.configure(text=f"✓ {os.path.basename(folder)}")
            else:
                files = self._browse_files([("Excel", "*.xlsx *.xls"), ("CSV", "*.csv")])
                if files:
                    self.sales_file = files[0]
                    self.file2_label.configure(text=f"✓ {os.path.basename(self.sales_file)}")

    def _select_xml_folder(self, files=None):
        folder = self._browse_folder()
        if folder:
            self.xml_folder = folder
            self.file3_label.configure(text=f"✓ {os.path.basename(folder)}")

    def _run_reconcile(self):
        if not self.extract_file:
            self.status_label.configure(text="Selecione o extrato bancário")
            return

        task_id, error = self.task_helper.start_task({})
        if error:
            messagebox.showwarning("Aviso", error)
            return
        self._task_id = task_id

        try:
            tolerance = float(self.tolerance_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Tolerância inválida. Use um número (ex: 0.05)")
            self.task_helper.cancel()
            return

        if self.mode == "nfe":
            if not self.xml_folder:
                self.status_label.configure(text="Selecione a pasta com XMLs de NF-e")
                self.task_helper.cancel()
                return

            output_path = self._create_output_path("conciliacao_nfe.xlsx")
            if not output_path:
                self.task_helper.cancel()
                return

            if not self.start_execution():
                self.task_helper.cancel()
                return

            extract_file = self.extract_file
            xml_folder = self.xml_folder

            theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
            visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

            def execute():
                conc = Conciliador()
                return conc.reconcile_nfe(xml_folder, extract_file, output_path, tolerance=tolerance, visual_theme=visual_theme)

            def on_complete(result):
                self.after(0, lambda: self._on_nfe_done(result, output_path))

            g_id, g_err = global_executor.submit(
                tool_name="conciliador",
                tool_display_name="Conciliador Pro",
                execute_func=execute,
                on_complete=on_complete,
                user_id=self.user_id,
            )
            if g_err:
                messagebox.showwarning("Aviso", g_err)
        else:
            if not self.sales_file:
                self.status_label.configure(text="Selecione a planilha de vendas")
                self.task_helper.cancel()
                return

            output_path = self._create_output_path("conciliacao.xlsx")
            if not output_path:
                self.task_helper.cancel()
                return

            if not self.start_execution():
                return

            extract_file = self.extract_file
            sales_file = self.sales_file

            theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
            visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

            def execute():
                conc = Conciliador()
                return conc.reconcile_classic(extract_file, sales_file, output_path, tolerance=tolerance, visual_theme=visual_theme)

            def on_complete(result):
                self.after(0, lambda: self._on_classic_done(result, output_path))

            g_id, g_err = global_executor.submit(
                tool_name="conciliador",
                tool_display_name="Conciliador Pro",
                execute_func=execute,
                on_complete=on_complete,
                user_id=self.user_id,
            )
            if g_err:
                messagebox.showwarning("Aviso", g_err)

    def _on_nfe_done(self, result, output_path):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        rows = result.get('matched', 0) + result.get('unmatched_nfe', 0)

        if result.get("success"):
            self._finalize_execution(result, output_path, rows, {"linhas": rows})
            messagebox.showinfo(
                "Conciliação NF-e Concluída",
                f"✅ Notas fiscais conciliadas: {result.get('matched')}\n"
                f"⏳ Notas pendentes (não pagas): {result.get('unmatched_nfe')}\n"
                f"💰 Transações bancárias sem NF: {result.get('unmatched_bank')}\n\n"
                f"Arquivo salvo em: {result.get('output_path')}"
            )
        else:
            self._finalize_execution(result, output_path, rows)
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        self.status_label.configure(text="")
        self._reset_files()

    def _on_classic_done(self, result, output_path):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        rows = result.get('matched', 0) + result.get('unmatched_extract', 0) + result.get('unmatched_sales', 0)

        if result.get("success"):
            self._finalize_execution(result, output_path, rows, {"linhas": rows})
            messagebox.showinfo(
                "Conciliação Concluída",
                f"✅ Conciliados: {result.get('matched')}\n"
                f"⏳ Pendentes no extrato: {result.get('unmatched_extract')}\n"
                f"⏳ Pendentes nas vendas: {result.get('unmatched_sales')}\n\n"
                f"Arquivo salvo em: {result.get('output_path')}"
            )
        else:
            self._finalize_execution(result, output_path, rows)
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        self.status_label.configure(text="")
        self._reset_files()
