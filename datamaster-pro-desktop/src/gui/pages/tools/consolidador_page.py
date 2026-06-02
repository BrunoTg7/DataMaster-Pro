import customtkinter as ctk
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.consolidador.consolidador_v2 import Consolidador
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


class ConsolidadorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.consolidador = Consolidador()
        self.task_helper = TaskHelper("consolidador")
        self.execution = ExecutionHelper("consolidador", "Consolidador", user_id)
        self._task_id = None
        self._cancelled_by_user = False
        super().__init__(master, "consolidador", "Consolidador", on_back, execution_tracker, user_id)
        self._check_task_state()

    def _check_task_state(self):
        storage = self.task_helper.storage
        last_task = storage.get_last_task_by_tool("consolidador")

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

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Selecione múltiplos arquivos de dados (Excel, CSV, TXT ou JSON) para consolidar em uma planilha única estruturada com formatação comercial premium.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=500
        )
        info.pack(pady=(20, 10))

        self.drop_frame = self._create_drop_zone(
            content,
            "Selecione ou arraste arquivos para consolidar",
            self._select_files
        )

        self.file_list_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.file_list_frame.pack(fill="x", padx=20, pady=10)

        options_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        options_frame.pack(fill="x", padx=20, pady=10)
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)

        left_options = ctk.CTkFrame(options_frame, fg_color="transparent")
        left_options.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        lbl_strategy = ctk.CTkLabel(
            left_options,
            text="Estratégia de Consolidação:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl_strategy.pack(anchor="w", pady=(0, 5))

        self.merge_strategy = ctk.CTkSegmentedButton(
            left_options,
            values=["concat", "merge", "join"],
            selected_color=config.Colors.PRIMARY,
            command=self._on_strategy_change
        )
        self.merge_strategy.set("concat")
        self.merge_strategy.pack(fill="x", pady=(0, 15))

        self.join_options_frame = ctk.CTkFrame(left_options, fg_color="transparent")

        lbl_key = ctk.CTkLabel(
            self.join_options_frame,
            text="Coluna Chave (Join Key):",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_key.pack(anchor="w")

        self.join_key_entry = ctk.CTkEntry(
            self.join_options_frame,
            placeholder_text="Ex: SKU, ID, CPF, Codigo"
        )
        self.join_key_entry.pack(fill="x", pady=(0, 10))

        lbl_join_type = ctk.CTkLabel(
            self.join_options_frame,
            text="Tipo de Cruzamento (Join):",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_join_type.pack(anchor="w")

        self.join_type_menu = ctk.CTkOptionMenu(
            self.join_options_frame,
            values=["left", "inner", "right", "outer"],
            fg_color=config.Colors.BACKGROUND,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER
        )
        self.join_type_menu.set("left")
        self.join_type_menu.pack(fill="x", pady=(0, 10))

        lbl_sheet = ctk.CTkLabel(
            left_options,
            text="Extração de Abas (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl_sheet.pack(anchor="w", pady=(5, 5))

        self.sheet_selection_menu = ctk.CTkOptionMenu(
            left_options,
            values=["Primeira Aba", "Todas as Abas", "Especificar Nome"],
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER,
            command=self._on_sheet_selection_change
        )
        self.sheet_selection_menu.set("Primeira Aba")
        self.sheet_selection_menu.pack(fill="x", pady=(0, 5))

        self.sheet_name_entry = ctk.CTkEntry(
            left_options,
            placeholder_text="Nome exato da aba (ex: Vendas)"
        )

        right_options = ctk.CTkFrame(options_frame, fg_color="transparent")
        right_options.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        lbl_intelligence = ctk.CTkLabel(
            right_options,
            text="Inteligência de Dados:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl_intelligence.pack(anchor="w", pady=(0, 5))

        self.fuzzy_switch = ctk.CTkSwitch(
            right_options,
            text="Alinhamento Inteligente de Cabeçalhos (Fuzzy)",
            progress_color=config.Colors.PRIMARY
        )
        self.fuzzy_switch.select()
        self.fuzzy_switch.pack(anchor="w", pady=(0, 10))

        self.duplicates_checkbox = ctk.CTkCheckBox(
            right_options,
            text="Remover registros duplicados da consolidação",
            border_color=config.Colors.BORDER,
            hover_color=config.Colors.PRIMARY,
            fg_color=config.Colors.PRIMARY
        )
        self.duplicates_checkbox.pack(anchor="w", pady=(0, 15))

        lbl_theme = ctk.CTkLabel(
            right_options,
            text="Tema Visual da Planilha (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl_theme.pack(anchor="w", pady=(5, 5))
        
        # Verificar se é usuário FREE
        user_plan = self.user_data.get("plan", "gratis").lower() if self.user_data else "gratis"
        is_free_user = user_plan == "gratis"
        
        if is_free_user:
            # Mostrar aviso para FREE users
            aviso_frame = ctk.CTkFrame(right_options, fg_color="transparent")
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
            right_options,
            values=["Azul Corporativo", "Verde Esmeralda", "Laranja Moderno", "Cinza Minimalista"],
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER
        )
        self.visual_theme_menu.set("Azul Corporativo")
        self.visual_theme_menu.pack(anchor="w", pady=(0, 15))
        
        # Desabilitar menu para FREE users
        if is_free_user:
            self.visual_theme_menu.configure(state="disabled")

        self.action_btn = self._create_action_button(content, "Consolidar Arquivos", self._run_consolidate)

        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)

    def _select_files(self, files=None):
        if files:
            self.uploaded_files = files
            self._update_file_list()
        else:
            files = self._browse_files([
                ("Arquivos de Planilhas", "*.xlsx *.xls *.csv *.txt *.json"),
                ("Pastas de Trabalho Excel", "*.xlsx *.xls"),
                ("Valores Separados por Vírgula (CSV)", "*.csv"),
                ("Arquivos de Texto Delimitados (TXT)", "*.txt"),
                ("Arquivos de Estrutura JSON", "*.json"),
                ("Todos os Arquivos", "*.*")
            ])
            if files:
                self.uploaded_files = files
                self._update_file_list()

    def _update_file_list(self):
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        if self.uploaded_files:
            header_frame = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
            header_frame.pack(fill="x")

            lbl = ctk.CTkLabel(
                header_frame,
                text=f"Arquivos Selecionados: {len(self.uploaded_files)}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY
            )
            lbl.pack(side="left")

            clear_all_btn = ctk.CTkButton(
                header_frame,
                text="Limpar todos",
                width=90,
                height=24,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color="#e74c3c",
                text_color="#e74c3c",
                border_width=1,
                border_color="#e74c3c",
                corner_radius=4,
                command=self._clear_all_files
            )
            clear_all_btn.pack(side="right")

            scroll = ctk.CTkScrollableFrame(self.file_list_frame, fg_color=config.Colors.CARD, height=100)
            scroll.pack(fill="x", pady=5)

            for i, f in enumerate(self.uploaded_files):
                file_row = ctk.CTkFrame(scroll, fg_color="transparent")
                file_row.pack(fill="x", padx=10, pady=2)

                file_lbl = ctk.CTkLabel(
                    file_row,
                    text=f"📄 {os.path.basename(f)} ({os.path.dirname(f)[:50]}...)",
                    font=ctk.CTkFont(size=11),
                    text_color=config.Colors.TEXT_SECONDARY
                )
                file_lbl.pack(side="left")

                remove_btn = ctk.CTkButton(
                    file_row,
                    text="✕",
                    width=20,
                    height=18,
                    font=ctk.CTkFont(size=8, weight="bold"),
                    fg_color="transparent",
                    hover_color="#e74c3c",
                    text_color="#a0a0a0",
                    corner_radius=3,
                    command=lambda idx=i: self._remove_file_at(idx)
                )
                remove_btn.pack(side="right", padx=(4, 0))

    def _clear_all_files(self):
        self.uploaded_files = []
        self._update_file_list()

    def _remove_file_at(self, index):
        if 0 <= index < len(self.uploaded_files):
            del self.uploaded_files[index]
            self._update_file_list()

    def _on_strategy_change(self, value):
        if value == "join":
            self.join_options_frame.pack(fill="x", pady=(0, 10))
        else:
            self.join_options_frame.pack_forget()

    def _on_sheet_selection_change(self, value):
        if value == "Especificar Nome":
            self.sheet_name_entry.pack(fill="x", pady=(5, 10))
        else:
            self.sheet_name_entry.pack_forget()

    def _run_consolidate(self):
        if not self.uploaded_files:
            self._safe_status("Erro: Selecione pelo menos um arquivo para consolidar.")
            return

        strategy = self.merge_strategy.get()
        join_key = self.join_key_entry.get().strip() if strategy == "join" else None

        if strategy == "join" and not join_key:
            self._safe_status("Erro: Informe a coluna chave para realizar o cruzamento.")
            return

        # Para evitar travamento da interface (Main Thread), não efetuamos leitura pandas sincrona
        # Verificamos apenas os limites de uso (Hit limits). O corte real de linhas será 
        # imposto diretamente no background pelo Consolidador.
        can_execute = self.start_execution(rows_to_process=0)
        if not can_execute:
            return

        user_plan = self.user_data.get("plan", "gratis").lower() if self.user_data else "gratis"
        max_allowed_rows = 600 if user_plan == "gratis" else 1000000

        output_path = self._create_output_path("consolidado.xlsx")
        if not output_path:
            return

        self._cancelled_by_user = False

        theme_map = {
            "Azul Corporativo": "classic_blue",
            "Verde Esmeralda": "emerald_green",
            "Laranja Moderno": "modern_orange",
            "Cinza Minimalista": "slate_gray"
        }
        visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

        sheet_sel = self.sheet_selection_menu.get()
        if sheet_sel == "Primeira Aba":
            sheet_selection = "first"
        elif sheet_sel == "Todas as Abas":
            sheet_selection = "all"
        else:
            sheet_selection = self.sheet_name_entry.get().strip() or "first"

        files = list(self.uploaded_files)
        fuzzy = self.fuzzy_switch.get()
        dup = self.duplicates_checkbox.get()
        join_type = self.join_type_menu.get()

        self._safe_status("⏳ Consolidando e formatando planilhas...")

        extra = dict(
            output_path=output_path,
            rows_processed=0,
            files=len(files),
            total_rows=0,
        )

        def execute():
            cons = Consolidador()
            return cons.consolidate(
                files,
                output_path,
                merge_strategy=strategy,
                max_rows=max_allowed_rows,
                sheet_selection=sheet_selection,
                enable_fuzzy_mapping=fuzzy,
                join_key=join_key,
                join_type=join_type,
                visual_theme=visual_theme,
                remove_duplicates=dup,
            )

        def on_complete(result):
            self.after(0, lambda: self._on_consolidate_done(result, extra, output_path, files))

        g_task_id, g_err = task_executor.submit(
            tool_name="consolidador",
            tool_display_name="Consolidador",
            execute_func=execute,
            on_complete=on_complete,
            user_id=self.user_id,
        )
        if g_err:
            from tkinter import messagebox
            messagebox.showwarning("Aviso", g_err)

    def _on_consolidate_done(self, result, extra, output_path, files):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        rows = result.get("total_rows", 0)
        extra["total_rows"] = rows
        self._finalize_execution(result, output_path, rows,
                                 {"registros": rows, "arquivos": len(files)})

        self._show_result(result)
        self._safe_status("")

        if result.get("success"):
            self.uploaded_files = []
            self._update_file_list()

        self._task_id = None

    def _safe_status(self, text):
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=text)
        except Exception:
            pass
