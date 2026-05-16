"""
Consolidador Page - Une múltiplas planilhas
"""
import customtkinter as ctk
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.consolidador.consolidador_v2 import Consolidador


class ConsolidadorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.consolidador = Consolidador()
        super().__init__(master, "consolidador", "Consolidador", on_back, execution_tracker, user_id)

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Selecione múltiplos arquivos Excel ou CSV para unificar em uma única planilha.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        self.drop_frame = self._create_drop_zone(
            content,
            "Selecione os arquivos para consolidar",
            self._select_files
        )

        self.file_list_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.file_list_frame.pack(fill="x", padx=20, pady=10)

        options_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        options_frame.pack(fill="x", padx=20, pady=10)

        lbl = ctk.CTkLabel(
            options_frame,
            text="Estratégia de merge:",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.merge_strategy = ctk.CTkSegmentedButton(
            options_frame,
            values=["concat", "merge"],
            selected_color=config.Colors.PRIMARY,
            command=self._on_strategy_change
        )
        self.merge_strategy.set("concat")
        self.merge_strategy.pack(padx=20, pady=(0, 15))

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
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Todos", "*.*")
            ])
            if files:
                self.uploaded_files = files
                self._update_file_list()

    def _update_file_list(self):
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        if self.uploaded_files:
            lbl = ctk.CTkLabel(
                self.file_list_frame,
                text=f"Arquivos selecionados: {len(self.uploaded_files)}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY
            )
            lbl.pack(anchor="w")

            for f in self.uploaded_files:
                file_lbl = ctk.CTkLabel(
                    self.file_list_frame,
                    text=f"• {os.path.basename(f)}",
                    font=ctk.CTkFont(size=11),
                    text_color=config.Colors.TEXT_SECONDARY
                )
                file_lbl.pack(anchor="w", padx=10, pady=2)

    def _on_strategy_change(self, value):
        pass

    def _run_consolidate(self):
        if not self.uploaded_files:
            self.status_label.configure(text="Selecione pelo menos um arquivo")
            return

        total_lines = 0
        try:
            import pandas as pd
            for f in self.uploaded_files:
                try:
                    if f.endswith('.csv'):
                        df = pd.read_csv(f, nrows=1000)
                        total_lines += len(df) * 2
                    else:
                        df = pd.read_excel(f, nrows=1000)
                        total_lines += len(df) * 2
                except:
                    pass
        except:
            pass

        allowed_rows = self.start_execution(rows_to_process=total_lines)
        if allowed_rows == 0: return

        output_path = self._create_output_path("consolidado.xlsx")
        if not output_path: return

        self.status_label.configure(text="Processando...")
        self.update()

        result = self.consolidador.consolidate(
            self.uploaded_files,
            output_path,
            merge_strategy=self.merge_strategy.get(),
            max_rows=allowed_rows
        )

        status = "completed" if result.get("success") else "failed"
        self.track_execution(output_path, status, rows_processed=result.get("total_rows", 0))

        self._show_result(result)
        self.status_label.configure(text="")

        if result.get("success"):
            self.uploaded_files = []
            self._update_file_list()