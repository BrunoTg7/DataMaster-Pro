import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.conciliador.conciliador_v2 import Conciliador
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


class ConciliadorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.conciliador = Conciliador(log_callback=self._log_msg)
        self.execution = ExecutionHelper("conciliador", "Conciliador Pro", user_id)
        self.extract_file = ""
        self.sales_file = ""
        self.xml_folder = ""
        self.mode = "classic"
        super().__init__(master, "conciliador", "Conciliador Pro", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.log_messages = []

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("conciliador")

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
        nfe_radio.pack(anchor="w", padx=20, pady=2)

        nfe_vendas_radio = ctk.CTkRadioButton(
            mode_frame,
            text="NF-e + Vendas (XML ↔ Planilha de Vendas)",
            variable=self.mode_var,
            value="nfe_vendas",
            command=self._toggle_mode,
            font=ctk.CTkFont(size=12)
        )
        nfe_vendas_radio.pack(anchor="w", padx=20, pady=(0, 15))

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

        self.file1_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.file1_frame.pack(pady=(0, 5))

        self.file1_label = ctk.CTkLabel(
            self.file1_frame,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file1_label.pack(side="left")

        self.file1_clear_btn = ctk.CTkButton(
            self.file1_frame,
            text="✕",
            width=24,
            height=20,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent",
            hover_color="#e74c3c",
            text_color="#a0a0a0",
            corner_radius=3,
            command=self._clear_file1
        )
        self.file1_clear_btn.pack(side="left", padx=(6, 0))
        self.file1_clear_btn.pack_forget()

        self.file2_drop = self._create_drop_zone(
            content,
            "Selecione o segundo arquivo",
            self._select_file2
        )
        self.file2_drop.pack(fill="x", padx=20, pady=10)

        self.file2_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.file2_frame.pack(pady=(0, 5))

        self.file2_label = ctk.CTkLabel(
            self.file2_frame,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file2_label.pack(side="left")

        self.file2_clear_btn = ctk.CTkButton(
            self.file2_frame,
            text="✕",
            width=24,
            height=20,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent",
            hover_color="#e74c3c",
            text_color="#a0a0a0",
            corner_radius=3,
            command=self._clear_file2
        )
        self.file2_clear_btn.pack(side="left", padx=(6, 0))
        self.file2_clear_btn.pack_forget()

        self.file3_drop = self._create_drop_zone(
            content,
            "Selecione pasta com XMLs (NF-e)",
            self._select_xml_folder
        )
        self.file3_drop.pack_forget()

        self.file3_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.file3_frame.pack_forget()

        self.file3_label = ctk.CTkLabel(
            self.file3_frame,
            text="Nenhuma pasta selecionada",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file3_label.pack(side="left")

        self.file3_clear_btn = ctk.CTkButton(
            self.file3_frame,
            text="✕",
            width=24,
            height=20,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent",
            hover_color="#e74c3c",
            text_color="#a0a0a0",
            corner_radius=3,
            command=self._clear_file3
        )
        self.file3_clear_btn.pack(side="left", padx=(6, 0))
        self.file3_clear_btn.pack_forget()

        self.options_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        self.options_frame.pack(fill="x", padx=20, pady=10)

        # Linha: Tolerância + Tema lado a lado
        row = ctk.CTkFrame(self.options_frame, fg_color="transparent")
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
        
        # Verificar se é usuário FREE
        user_plan = self.user_data.get("plan", "gratis").lower() if self.user_data else "gratis"
        is_free_user = user_plan == "gratis"
        
        if is_free_user:
            # Mostrar aviso para FREE users
            aviso_frame = ctk.CTkFrame(right, fg_color="transparent")
            aviso_frame.pack(anchor="w", pady=(0, 5))
            
            aviso_label = ctk.CTkLabel(
                aviso_frame,
                text="🔒 Tema único no plano Grátis (Azul Corporativo)",
                font=ctk.CTkFont(size=10),
                text_color="#F59E0B"
            )
            aviso_label.pack(anchor="w")
            
            upgrade_label = ctk.CTkLabel(
                aviso_frame,
                text="Upgrade para PRO para acessar 3 temas adicionais →",
                font=ctk.CTkFont(size=9),
                text_color=config.Colors.TEXT_SECONDARY
            )
            upgrade_label.pack(anchor="w")

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
        
        # Desabilitar menu para FREE users
        if is_free_user:
            self.visual_theme_menu.configure(state="disabled")

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

        # Acessa os labels de cada drop zone via winfo_children
        # children[0]=ícone, children[1]=label, children[2]=sublabel, children[3]=botão
        def set_label(frame, text):
            children = frame.winfo_children()
            if len(children) > 1:
                children[1].configure(text=text)

        def set_sublabel(frame, text):
            children = frame.winfo_children()
            if len(children) > 2:
                children[2].configure(text=text)

        if self.mode == "nfe_vendas":
            self.info_label.configure(text="Cruze XMLs de Notas Fiscais (NF-e) com a planilha de vendas do marketplace para verificar pedidos com e sem nota.")
            set_label(self.file1_drop, "1. Selecione a Pasta com XMLs (NF-e)")
            set_label(self.file2_drop, "2. Selecione a Planilha de Vendas")
            set_sublabel(self.file2_drop, "Planilha do ML, Shopee, etc.")
            set_label(self.file3_drop, "3. (Opcional) Selecione planilha de vendas")
            set_sublabel(self.file3_drop, "Para cruzar também com as vendas")
            self.file3_drop.pack_forget()
            self.file3_frame.pack_forget()
        elif self.mode == "nfe":
            self.info_label.configure(text="Cruze XMLs de Notas Fiscais (NF-e) com o extrato bancário para ver quais notas foram pagas.")
            set_label(self.file1_drop, "1. Selecione o Extrato Bancário")
            set_label(self.file2_drop, "2. Selecione a Pasta com XMLs")
            set_sublabel(self.file2_drop, "Clique para escolher a pasta")
            set_label(self.file3_drop, "3. (Opcional) Selecione planilha de vendas")
            set_sublabel(self.file3_drop, "Para cruzar também com as vendas")
            self.file3_drop.pack(fill="x", padx=20, pady=10, before=self.options_frame)
            self.file3_frame.pack(pady=(0, 5), before=self.options_frame)
        else:
            self.info_label.configure(text="Cruze extratos bancários (OFX/CSV/XLSX) com planilhas de vendas para encontrar divergências.")
            set_label(self.file1_drop, "1. Selecione o Extrato Bancário")
            set_label(self.file2_drop, "2. Selecione a Planilha de Vendas")
            set_sublabel(self.file2_drop, "Arraste arquivos aqui ou clique no botão")
            set_label(self.file3_drop, "Selecione pasta com XMLs (NF-e)")
            set_sublabel(self.file3_drop, "Clique no botão para selecionar arquivos")
            self.file3_drop.pack_forget()
            self.file3_frame.pack_forget()

    def _clear_file1(self):
        self.extract_file = ""
        self.xml_folder = ""
        self.file1_label.configure(text="Nenhum arquivo selecionado")
        self.file1_clear_btn.pack_forget()

    def _clear_file2(self):
        self.sales_file = ""
        self.xml_folder = ""
        self.file2_label.configure(text="Nenhum arquivo selecionado")
        self.file2_clear_btn.pack_forget()

    def _clear_file3(self):
        self.xml_folder = ""
        self.file3_label.configure(text="Nenhuma pasta selecionada")
        self.file3_clear_btn.pack_forget()

    def _reset_files(self):
        self._clear_file1()
        self._clear_file2()
        self._clear_file3()

    def _select_file1(self, files=None):
        if self.mode == "nfe_vendas":
            if files:
                self.xml_folder = files[0]
                self.file1_label.configure(text=f"✓ {os.path.basename(self.xml_folder)}")
                self.file1_clear_btn.pack(side="left", padx=(6, 0))
            else:
                folder = self._browse_folder()
                if folder:
                    self.xml_folder = folder
                    self.file1_label.configure(text=f"✓ {os.path.basename(folder)}")
                    self.file1_clear_btn.pack(side="left", padx=(6, 0))
        elif files:
            self.extract_file = files[0]
            self.file1_label.configure(text=f"✓ {os.path.basename(self.extract_file)}")
            self.file1_clear_btn.pack(side="left", padx=(6, 0))
        else:
            filetypes = [
                ("Todos os arquivos", "*"),
                ("Excel", "*.xlsx;*.xls"),
                ("CSV", "*.csv"),
                ("OFX (extrato)", "*.ofx"),
            ]
            files = self._browse_files(filetypes)
            if files:
                self.extract_file = files[0]
                self.file1_label.configure(text=f"✓ {os.path.basename(self.extract_file)}")
                self.file1_clear_btn.pack(side="left", padx=(6, 0))

    def _select_file2(self, files=None):
        if files:
            if self.mode == "nfe":
                self.xml_folder = files[0]
                self.file2_label.configure(text=f"✓ {os.path.basename(self.xml_folder)}")
                self.file2_clear_btn.pack(side="left", padx=(6, 0))
            else:
                self.sales_file = files[0]
                self.file2_label.configure(text=f"✓ {os.path.basename(self.sales_file)}")
                self.file2_clear_btn.pack(side="left", padx=(6, 0))
        else:
            if self.mode == "nfe":
                folder = self._browse_folder()
                if folder:
                    self.xml_folder = folder
                    self.file2_label.configure(text=f"✓ {os.path.basename(folder)}")
                    self.file2_clear_btn.pack(side="left", padx=(6, 0))
            else:
                files = self._browse_files([("Todos os arquivos", "*"), ("Excel", "*.xlsx;*.xls"), ("CSV", "*.csv")])
                if files:
                    self.sales_file = files[0]
                    self.file2_label.configure(text=f"✓ {os.path.basename(self.sales_file)}")
                    self.file2_clear_btn.pack(side="left", padx=(6, 0))

    def _select_xml_folder(self, files=None):
        folder = self._browse_folder()
        if folder:
            self.xml_folder = folder
            self.file3_label.configure(text=f"✓ {os.path.basename(folder)}")
            self.file3_clear_btn.pack(side="left", padx=(6, 0))
            self.file3_frame.pack(pady=(0, 5))

    def _run_reconcile(self):
        if not self.extract_file:
            self.status_label.configure(text="Selecione o extrato bancário")
            return

        try:
            tolerance = float(self.tolerance_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Tolerância inválida. Use um número (ex: 0.05)")
            return

        if self.mode == "nfe_vendas":
            if not self.xml_folder:
                self.status_label.configure(text="Selecione a pasta com XMLs de NF-e")
                return
            if not self.sales_file:
                self.status_label.configure(text="Selecione a planilha de vendas")
                return

            output_path = self._create_output_path("conciliacao_nfe_vendas.xlsx")
            if not output_path:
                return

            if not self.start_execution():
                return

            xml_folder = self.xml_folder
            sales_file = self.sales_file

            theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
            visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

            def execute():
                conc = Conciliador()
                return conc.reconcile_nfe_vendas(xml_folder, sales_file, output_path, tolerance=tolerance, visual_theme=visual_theme)

            def on_complete(result):
                self.after(0, lambda: self._on_nfe_vendas_done(result, output_path))

            g_id, g_err = task_executor.submit(
                tool_name="conciliador",
                tool_display_name="Conciliador Pro",
                execute_func=execute,
                on_complete=on_complete,
                user_id=self.user_id,
            )
            if g_err:
                messagebox.showwarning("Aviso", g_err)
        elif self.mode == "nfe":
            if not self.xml_folder:
                self.status_label.configure(text="Selecione a pasta com XMLs de NF-e")
                return

            output_path = self._create_output_path("conciliacao_nfe.xlsx")
            if not output_path:
                return

            if not self.start_execution():
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

            g_id, g_err = task_executor.submit(
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
                return

            output_path = self._create_output_path("conciliacao.xlsx")
            if not output_path:
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

            g_id, g_err = task_executor.submit(
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

    def _on_nfe_vendas_done(self, result, output_path):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        rows = result.get("ok", 0) + result.get("divergentes", 0) + result.get("faltando", 0) + result.get("sem_nota", 0)

        if result.get("success"):
            self._finalize_execution(result, output_path, rows, {"ok": result.get("ok", 0), "divergentes": result.get("divergentes", 0)})
            messagebox.showinfo(
                "Conciliação NF-e + Vendas Concluída",
                f"✅ OK: {result.get('ok')}\n"
                f"⚠️ Divergentes: {result.get('divergentes')}\n"
                f"❌ Faltando: {result.get('faltando')}\n"
                f"📋 Pedidos sem nota: {result.get('sem_nota')}\n\n"
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
