"""
Categorizador Page - Classifica transações por palavras-chave
"""
import customtkinter as ctk
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.categorizador.categorizador_v2 import Categorizador
from src.gui.components.result_viewer_modal import ResultViewerButton


class CategoryBar(ctk.CTkFrame):
    """Barra de categoria horizontal"""
    def __init__(self, parent, category_name, count, percentage, color, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(1, weight=1)

        name_lbl = ctk.CTkLabel(
            self,
            text=f"  {category_name.upper()}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY,
            anchor="w",
            width=120
        )
        name_lbl.grid(row=0, column=0, padx=(0, 10), sticky="w")

        bar_bg = ctk.CTkFrame(self, fg_color=config.Colors.BORDER, height=20, corner_radius=4)
        bar_bg.grid(row=0, column=1, sticky="ew")
        bar_bg.grid_columnconfigure(0, weight=1)

        bar_fill = ctk.CTkFrame(bar_bg, fg_color=color, height=20, corner_radius=4)
        bar_fill.grid(row=0, column=0, sticky="w", padx=0)
        bar_fill.configure(width=int(percentage * 2))

        count_lbl = ctk.CTkLabel(
            self,
            text=f"{count} ({percentage:.1f}%)",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            width=80
        )
        count_lbl.grid(row=0, column=2, padx=(10, 0))


class ResultDashboard(ctk.CTkFrame):
    """Dashboard de resultados da categorização"""
    def __init__(self, parent, result, suggestions, on_close, on_apply_suggestions):
        super().__init__(parent, fg_color=config.Colors.BACKGROUND, corner_radius=16)

        self.result = result
        self.suggestions = suggestions
        self.on_close = on_close
        self.on_apply_suggestions = on_apply_suggestions

        self._create_widgets()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="✅ Resultado da Categorização",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=datetime.now().strftime("%d/%m/%Y %H:%M"),
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        ).grid(row=0, column=1, sticky="e")

        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_columnconfigure(1, weight=1)
        main_content.grid_rowconfigure(0, weight=1)

        left_col = ctk.CTkFrame(main_content, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_col.grid_columnconfigure(0, weight=1)

        right_col = ctk.CTkFrame(main_content, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_col.grid_columnconfigure(0, weight=1)

        self._create_stats_cards(left_col)
        self._create_chart_section(left_col)

        if self.suggestions:
            self._create_suggestions_section(right_col)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=(10, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        if self.suggestions:
            apply_btn = ctk.CTkButton(
                btn_frame,
                text="✓ Aplicar Sugestões",
                command=self._on_apply,
                width=200,
                height=45,
                fg_color=config.Colors.PRIMARY,
                hover_color=config.Colors.PRIMARY_HOVER,
                font=ctk.CTkFont(size=14, weight="bold"),
                corner_radius=8
            )
            apply_btn.grid(row=0, column=0, sticky="w", padx=(0, 10))

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Fechar",
            command=self.on_close,
            width=150,
            height=45,
            fg_color="transparent",
            border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_SECONDARY,
            font=ctk.CTkFont(size=14),
            corner_radius=8
        )
        close_btn.grid(row=0, column=1, sticky="e")

    def _create_stats_cards(self, parent):
        stats_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        stats_frame.pack(fill="x", pady=(0, 15))
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)

        total = self.result.get("total_rows", 0)
        categorized = self.result.get("categorized_rows", 0)
        proc_time = self.result.get("processing_time", 0)
        time_saved = self.result.get("estimated_time_saved", 0)

        self._stat_card(stats_frame, "📄", "Total Linhas", str(total), 0)
        self._stat_card(stats_frame, "✅", "Categorizadas", str(categorized), 1)
        self._stat_card(stats_frame, "⚡", "Tempo", f"{proc_time}s", 2)

        roi_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        roi_frame.pack(fill="x")

        ctk.CTkLabel(
            roi_frame,
            text="💰 Tempo Economizado",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.PRIMARY
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            roi_frame,
            text=f"~{time_saved} minutos",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack()

        ctk.CTkLabel(
            roi_frame,
            text="de trabalho manual",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(pady=(0, 15))

    def _stat_card(self, parent, icon, title, value, col):
        frame = ctk.CTkFrame(parent, fg_color=config.Colors.BACKGROUND, corner_radius=8)
        frame.grid(row=0, column=col, padx=5, pady=15, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text=icon,
            font=ctk.CTkFont(size=24)
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack()

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(pady=(0, 10))

    def _create_chart_section(self, parent):
        chart_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        chart_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            chart_frame,
            text="📊 Distribuição por Categoria",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 10))

        bars_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        bars_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        bars_container.grid_columnconfigure(0, weight=1)

        counts = self.result.get("category_counts", {})
        total = self.result.get("total_rows", 1)

        colors = [
            "#d48214", "#3B82F6", "#10B981", "#8B5CF6",
            "#F59E0B", "#EF4444", "#EC4899", "#06B6D4"
        ]

        sorted_cats = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        for i, (cat, count) in enumerate(sorted_cats):
            if cat == "outros":
                continue
            pct = round(count / total * 100, 1)
            color = colors[i % len(colors)]

            bar = CategoryBar(
                bars_container,
                category_name=cat,
                count=count,
                percentage=pct,
                color=color
            )
            bar.grid(row=i, column=0, sticky="ew", pady=3)

    def _create_suggestions_section(self, parent):
        sug_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        sug_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            sug_frame,
            text="💡 Otimizações Sugeridas",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            sug_frame,
            text="Encontramos padrões na categoria 'outros':",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(sug_frame, fg_color="transparent", height=200)
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.sug_vars = {}

        for sug in self.suggestions:
            cat_name = sug["category"]
            count = sug["matches_count"]
            examples = sug["examples"][:3]

            sug_item = ctk.CTkFrame(scroll, fg_color=config.Colors.BACKGROUND, corner_radius=8)
            sug_item.pack(fill="x", pady=5)

            var = ctk.BooleanVar(value=True)
            self.sug_vars[cat_name] = var

            cb = ctk.CTkCheckBox(
                sug_item,
                text=f"{cat_name.upper()} ({count} matches)",
                variable=var,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY
            )
            cb.pack(anchor="w", padx=10, pady=(8, 3))

            ex_text = ", ".join([str(e)[:30] for e in examples])
            ctk.CTkLabel(
                sug_item,
                text=f"   Ex: {ex_text}...",
                font=ctk.CTkFont(size=10),
                text_color=config.Colors.TEXT_SECONDARY
            ).pack(anchor="w", padx=10, pady=(0, 8))

    def _on_apply(self):
        selected = {cat for cat, var in self.sug_vars.items() if var.get()}
        self.on_apply_suggestions(selected)
        self.on_close()


class CategorizadorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.categorizador = Categorizador()
        self.input_file = ""
        self.result_dashboard = None
        self._last_result_text = ""
        super().__init__(master, "categorizador", "Categorizador", on_back, execution_tracker, user_id)

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        self.input_section = ctk.CTkFrame(content, fg_color="transparent")
        self.input_section.pack(fill="both", expand=True)

        info = ctk.CTkLabel(
            self.input_section,
            text="Selecione uma planilha com transações para classificar automaticamente.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        self.drop_frame = self._create_drop_zone(
            self.input_section,
            "Selecione arquivo com transações",
            self._select_input_file
        )

        self.file_label = ctk.CTkLabel(
            self.input_section,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file_label.pack(pady=5)

        options_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        options_frame.pack(fill="x", padx=20, pady=10)

        col_lbl = ctk.CTkLabel(
            options_frame,
            text="Coluna com descrição:",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        col_lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.column_entry = ctk.CTkEntry(
            options_frame,
            width=300,
            placeholder_text="Ex: Descrição, Historico, Nome"
        )
        self.column_entry.pack(padx=20, pady=(0, 15))

        custom_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        custom_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            custom_frame,
            text="Carregar categorias customizadas (JSON/Excel):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkButton(
            custom_frame,
            text="📂 Carregar Arquivo de Categorias",
            command=self._load_custom_categories,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER
        ).pack(padx=20, pady=(0, 15))

        self.custom_label = ctk.CTkLabel(
            custom_frame,
            text="Usando categorias padrão",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.custom_label.pack(pady=(0, 10))

        cat_frame = ctk.CTkScrollableFrame(
            content,
            fg_color="transparent",
            height=200
        )
        cat_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.cat_title = ctk.CTkLabel(
            cat_frame,
            text="Categorias disponíveis:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        self.cat_title.pack(anchor="w", padx=10, pady=(0, 10))

        self.cat_labels = []
        self._update_category_display()

        self.action_btn = self._create_action_button(self.input_section, "Categorizar Transações", self._run_categorize)

        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)

    def _update_category_display(self):
        """Atualiza display das categorias"""
        for lbl in self.cat_labels:
            lbl.destroy()
        self.cat_labels = []

        categories = self.categorizador.get_categories()
        sorted_cats = sorted(categories.items(), key=lambda x: x[1].get("priority", 0), reverse=True)

        for cat, data in sorted_cats:
            if cat == "outros":
                continue
            priority = data.get("priority", 0)
            keywords = data.get("keywords", [])
            keywords_text = ", ".join(keywords[:4]) if keywords else "sem palavras-chave"

            lbl = ctk.CTkLabel(
                self.cat_title.master,
                text=f"⭐ {cat.upper()} (prio: {priority}): {keywords_text}",
                font=ctk.CTkFont(size=11),
                text_color=config.Colors.TEXT_SECONDARY
            )
            lbl.pack(anchor="w", padx=20, pady=2)
            self.cat_labels.append(lbl)

    def _load_custom_categories(self):
        files = self._browse_files([
            ("JSON", "*.json"),
            ("Excel", "*.xlsx *.xls")
        ])
        if files:
            result = self.categorizador.load_custom_categories_from_file(files[0])
            if result.get("success"):
                self.custom_label.configure(text=f"✓ Categorias carregadas: {len(result.get('categories', {}))}")
                self._update_category_display()
            else:
                self.status_label.configure(text=f"Erro: {result.get('error')}")

    def _select_input_file(self, files=None):
        if files:
            self.input_file = files[0]
            self.file_label.configure(text=f"✓ {os.path.basename(self.input_file)}")
        else:
            files = self._browse_files([
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv")
            ])
            if files:
                self.input_file = files[0]
                self.file_label.configure(text=f"✓ {os.path.basename(self.input_file)}")

    def _run_categorize(self):
        if not self.input_file:
            self.status_label.configure(text="Selecione um arquivo")
            return

        column = self.column_entry.get().strip()
        if not column:
            self.status_label.configure(text="Informe o nome da coluna de descrição")
            return

        output_path = self._create_output_path("categorizado.xlsx")
        if not output_path:
            return

        if not self.start_execution():
            return
        self.status_label.configure(text="Processando...")
        self.update()

        result = self.categorizador.categorize(
            self.input_file,
            output_path,
            description_column=column,
            category_column="categoria"
        )

        status = "completed" if result.get("success") else "failed"
        self.track_execution(output_path, status, rows_processed=result.get("total_rows", 0))

        if result.get("success"):
            suggestions = result.get("others_suggestions", [])
            self._show_result_dashboard(result, suggestions)
            self.input_file = ""
            self.file_label.configure(text="")
        else:
            from tkinter import messagebox
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        self.status_label.configure(text="")

    def _show_result_dashboard(self, result, suggestions):
        """Mostra dashboard de resultados"""
        if self.result_dashboard:
            self.result_dashboard.destroy()

        self.input_section.pack_forget()

        self.result_dashboard = ResultDashboard(
            self,
            result,
            suggestions,
            on_close=self._close_dashboard,
            on_apply_suggestions=self._apply_suggestions
        )
        self.result_dashboard.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)

    def _close_dashboard(self):
        """Fecha o dashboard e volta para a tela de entrada"""
        if self.result_dashboard:
            self.result_dashboard.destroy()
            self.result_dashboard = None

        self.input_section.pack(fill="both", expand=True)
        self._update_category_display()

    def _apply_suggestions(self, selected_categories):
        """Aplica as sugestões de categorias selecionadas"""
        for cat_name in selected_categories:
            sug = next((s for s in self.result_dashboard.suggestions if s["category"] == cat_name), None)
            if sug:
                keywords = sug["examples"][:5]
                self.categorizador.add_category(cat_name, keywords, priority=10)

        self.status_label.configure(text="✓ Categorias atualizadas!")

    def _show_suggestion_dialog(self, suggestions):
        """Mostra diálogo interativo de sugestões"""
        pass
