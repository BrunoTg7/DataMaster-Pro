"""
Categorizador Page - Classifica transações e textos por palavras-chave com regras inteligentes e multi-área
"""
import customtkinter as ctk
import os
import sys
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.categorizador.categorizador_v2 import Categorizador
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


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
        
        # Ajustar tamanho proporcional da barra
        width_px = max(int(percentage * 3.5), 5) # escala de largura
        bar_fill.configure(width=width_px)

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
            text="✅ Resultados & Descobertas",
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
                text="✓ Aplicar Regras Mineradas",
                command=self._on_apply,
                width=220,
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
        self._stat_card(stats_frame, "🏷️", "Categorizadas", str(categorized), 1)
        self._stat_card(stats_frame, "⚡", "Tempo", f"{proc_time}s", 2)

        roi_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        roi_frame.pack(fill="x")

        ctk.CTkLabel(
            roi_frame,
            text="💰 Tempo de Trabalho Economizado",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.Colors.PRIMARY
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            roi_frame,
            text=f"~{time_saved} minutos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack()

        ctk.CTkLabel(
            roi_frame,
            text="de classificação manual de planilhas economizada",
            font=ctk.CTkFont(size=10),
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
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack()

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=10),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(pady=(0, 10))

    def _create_chart_section(self, parent):
        chart_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        chart_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            chart_frame,
            text="📊 Distribuição Real por Categoria",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 10))

        bars_container = ctk.CTkScrollableFrame(chart_frame, fg_color="transparent", height=150)
        bars_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        bars_container.grid_columnconfigure(0, weight=1)

        counts = self.result.get("category_counts", {})
        total = self.result.get("total_rows", 1)

        colors = [
            "#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", 
            "#EF4444", "#EC4899", "#06B6D4", "#14B8A6"
        ]

        sorted_cats = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        idx = 0
        for cat, count in sorted_cats:
            if cat == "outros" and len(sorted_cats) > 1:
                continue
            pct = round(count / total * 100, 1)
            color = colors[idx % len(colors)]

            bar = CategoryBar(
                bars_container,
                category_name=cat,
                count=count,
                percentage=pct,
                color=color
            )
            bar.grid(row=idx, column=0, sticky="ew", pady=3)
            idx += 1
            
        # Adicionar "outros" no final
        if "outros" in counts and len(sorted_cats) > 1:
            pct = round(counts["outros"] / total * 100, 1)
            bar = CategoryBar(
                bars_container,
                category_name="outros",
                count=counts["outros"],
                percentage=pct,
                color="#6B7280"
            )
            bar.grid(row=idx, column=0, sticky="ew", pady=3)

    def _create_suggestions_section(self, parent):
        sug_frame = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=12)
        sug_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            sug_frame,
            text="💡 Regras Extraídas da Planilha",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.Colors.PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            sug_frame,
            text="Encontramos novos termos recorrentes para classificar:",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(sug_frame, fg_color="transparent", height=240)
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.sug_vars = {}

        for sug in self.suggestions:
            cat_name = sug["category"]
            count = sug.get("matches_count", 0)
            examples = sug["examples"][:3]

            sug_item = ctk.CTkFrame(scroll, fg_color=config.Colors.BACKGROUND, corner_radius=8)
            sug_item.pack(fill="x", pady=5)

            var = ctk.BooleanVar(value=True)
            self.sug_vars[cat_name] = var

            cb = ctk.CTkCheckBox(
                sug_item,
                text=f"{cat_name.upper()} ({count} ocorrências)",
                variable=var,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY,
                border_color=config.Colors.BORDER,
                fg_color=config.Colors.PRIMARY
            )
            cb.pack(anchor="w", padx=10, pady=(8, 3))

            ex_text = ", ".join([str(e)[:30] for e in examples])
            ctk.CTkLabel(
                sug_item,
                text=f"   Exemplo: {ex_text}...",
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
        self.execution = ExecutionHelper("categorizador", "Categorizador", user_id)
        super().__init__(master, "categorizador", "Categorizador", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.task_helper = TaskHelper("categorizador")

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("categorizador")
        
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

        self.input_section = ctk.CTkFrame(content, fg_color="transparent")
        self.input_section.pack(fill="both", expand=True)

        info = ctk.CTkLabel(
            self.input_section,
            text="Classifique planilhas de transações ou registros textuais em categorias de mercado com base em regras avançadas, Regex e palavras-chave negativas.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=500
        )
        info.pack(pady=(20, 10))

        # Dropzone do Arquivo de Entrada
        self.drop_frame = self._create_drop_zone(
            self.input_section,
            "Selecione o arquivo de transações/dados",
            self._select_input_file
        )

        self.file_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.file_frame.pack(pady=5)

        self.file_label = ctk.CTkLabel(
            self.file_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file_label.pack(side="left")

        self.file_clear_btn = ctk.CTkButton(
            self.file_frame,
            text="✕",
            width=24,
            height=20,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent",
            hover_color="#e74c3c",
            text_color="#a0a0a0",
            corner_radius=3,
            command=self._clear_input_file
        )
        self.file_clear_btn.pack(side="left", padx=(6, 0))
        self.file_clear_btn.pack_forget()

        # Configurações de Mapeamento de Coluna e Área de Negócio
        options_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        options_frame.pack(fill="x", padx=20, pady=10)

        col_lbl = ctk.CTkLabel(
            options_frame,
            text="Coluna com Descrição de Texto:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        col_lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.column_entry = ctk.CTkEntry(
            options_frame,
            width=350,
            placeholder_text="Ex: Descrição, Historico, Nome do Produto, Mensagem"
        )
        self.column_entry.pack(anchor="w", padx=20, pady=(0, 10))

        # Linha: Área + Tema lado a lado
        row = ctk.CTkFrame(options_frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(5, 15))

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(20, 0))

        ctk.CTkLabel(
            left,
            text="Área / Setor Setorial de Classificação:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 5))

        self.area_menu = ctk.CTkOptionMenu(
            left,
            values=[
                "Financeiro Pessoal",
                "Financeiro Empresarial (DRE)",
                "E-commerce & Vendas",
                "Atendimento ao Cliente (CRM)",
                "Recursos Humanos"
            ],
            fg_color=config.Colors.BACKGROUND,
            button_color=config.Colors.PRIMARY,
            text_color=config.Colors.TEXT_PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER,
            command=self._on_area_template_change
        )
        self.area_menu.set("Financeiro Pessoal")
        self.area_menu.pack(anchor="w")

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


        # Painel de Descoberta Automática de Categorias
        discovery_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        discovery_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            discovery_frame,
            text="🔍 Modo Descoberta Automática (Sem IA):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            discovery_frame,
            text="Carregue sua planilha e clique no botão abaixo para minerar os termos recorrentes e sugerir regras estruturadas.",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=480
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self.discover_btn = ctk.CTkButton(
            discovery_frame,
            text="⚡ Sugerir Categorias Desta Planilha",
            command=self._run_auto_discovery,
            fg_color="transparent",
            border_width=1,
            border_color=config.Colors.PRIMARY,
            text_color=config.Colors.TEXT_PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER
        )
        self.discover_btn.pack(anchor="w", padx=20, pady=(0, 15))

        # Carregar Regras Externas JSON/Excel
        custom_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        custom_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            custom_frame,
            text="Importar Regras Customizadas Externas (JSON/Excel):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkButton(
            custom_frame,
            text="📂 Importar Regras (.json/.xlsx)",
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

        # Categorias Ativas e Regras
        cat_frame = ctk.CTkScrollableFrame(
            content,
            fg_color="transparent",
            height=200
        )
        cat_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.cat_title = ctk.CTkLabel(
            cat_frame,
            text="Categorias e Regras Ativas de Classificação:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        self.cat_title.pack(anchor="w", padx=10, pady=(0, 10))

        self.cat_labels = []
        self._update_category_display()

        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)

        # Botão de Execução
        self.action_btn = self._create_action_button(content, "Categorizar Transações", self._run_categorize)

    def _update_category_display(self):
        """Atualiza display de categorias ativas na tela"""
        try:
            for lbl in self.cat_labels:
                if lbl.winfo_exists():
                    lbl.destroy()
            self.cat_labels = []
        except Exception:
            pass

        categories = self.categorizador.get_categories()
        sorted_cats = sorted(categories.items(), key=lambda x: x[1].get("priority", 0), reverse=True)

        for cat, data in sorted_cats:
            if cat == "outros":
                continue
            priority = data.get("priority", 0)
            keywords = data.get("keywords", [])
            negatives = data.get("negative_keywords", [])
            regexes = data.get("regex", [])
            
            keywords_text = ", ".join(keywords[:4]) if keywords else ""
            negatives_text = f" [exceto: {', '.join(negatives[:2])}]" if negatives else ""
            regex_text = f" [regex: {', '.join(regexes[:2])}]" if regexes else ""
            
            display_text = f"⭐ {cat.upper()} (prio: {priority}): "
            if keywords_text:
                display_text += keywords_text
            if negatives_text:
                display_text += negatives_text
            if regex_text:
                display_text += regex_text
            if not keywords_text and not regex_text:
                display_text += "sem regras básicas"

            lbl = ctk.CTkLabel(
                self.cat_title.master,
                text=display_text,
                font=ctk.CTkFont(size=11),
                text_color=config.Colors.TEXT_SECONDARY,
                wraplength=480,
                anchor="w",
                justify="left"
            )
            lbl.pack(anchor="w", padx=20, pady=2)
            self.cat_labels.append(lbl)

    def _on_area_template_change(self, val):
        mapping = {
            "Financeiro Pessoal": "financeiro_pessoal",
            "Financeiro Empresarial (DRE)": "financeiro_empresarial",
            "E-commerce & Vendas": "ecommerce",
            "Atendimento ao Cliente (CRM)": "crm_suporte",
            "Recursos Humanos": "recursos_humanos"
        }
        key = mapping.get(val, "financeiro_pessoal")
        self.categorizador.change_template(key)
        self.custom_label.configure(text=f"Usando template: {val}")
        self._update_category_display()

    def _load_custom_categories(self):
        files = self._browse_files([
            ("Ficheiros de Regras", "*.json *.xlsx *.xls"),
            ("JSON de Configuração", "*.json"),
            ("Planilha Excel de Regras", "*.xlsx *.xls")
        ])
        if files:
            result = self.categorizador.load_custom_categories_from_file(files[0])
            if result.get("success"):
                self.custom_label.configure(text=f"✓ Regras customizadas carregadas: {len(result.get('categories', {}))}")
                self._update_category_display()
            else:
                try:
                    if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                        self.status_label.configure(text=f"Erro ao carregar: {result.get('error')}")
                except Exception:
                    pass

    def _clear_input_file(self):
        self.input_file = ""
        self.file_label.configure(text="")
        self.file_clear_btn.pack_forget()

    def _select_input_file(self, files=None):
        if files:
            self.input_file = files[0]
            self.file_label.configure(text=f"✓ {os.path.basename(self.input_file)}")
            self.file_clear_btn.pack(side="left", padx=(6, 0))
        else:
            files = self._browse_files([
                ("Arquivos de Dados", "*.xlsx *.xls *.csv"),
                ("Pastas de Trabalho Excel", "*.xlsx *.xls"),
                ("Valores Separados por Vírgula", "*.csv")
            ])
            if files:
                self.input_file = files[0]
                self.file_label.configure(text=f"✓ {os.path.basename(self.input_file)}")
                self.file_clear_btn.pack(side="left", padx=(6, 0))

    def _run_auto_discovery(self):
        if not self.input_file:
            from tkinter import messagebox
            messagebox.showwarning("Aviso", "Selecione primeiro uma planilha de transações na zona de arquivos para poder analisá-la.")
            return
            
        column = self.column_entry.get().strip()
        if not column:
            from tkinter import messagebox
            messagebox.showwarning("Aviso", "Por favor, preencha a 'Coluna com descrição' para sabermos qual coluna minerar.")
            return
            
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="⏳ Minerando termos frequentes da planilha...")
            self.update()
            
            result = self.categorizador.discover_categories(self.input_file, column, num_categories=5)
            
            if result.get("success"):
                suggestions = result.get("suggestions", [])
                if not suggestions:
                    from tkinter import messagebox
                    messagebox.showinfo("Modo Descoberta", "Nenhum termo recorrente relevante pôde ser extraído.")
                    return
                # Mostrar o dashboard com as sugestões
                mock_result = {
                    "success": True, 
                    "total_rows": 100, 
                    "categorized_rows": 0, 
                    "category_counts": {}, 
                    "processing_time": 0.1, 
                    "estimated_time_saved": 0
                }
                self._show_result_dashboard(mock_result, suggestions)
            else:
                from tkinter import messagebox
                messagebox.showerror("Erro", result.get("error", "Erro ao executar a descoberta."))
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro", str(e))
        finally:
            try:
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    self.status_label.configure(text="")
            except Exception:
                pass

    def _run_categorize(self):
        if not self.input_file:
            try:
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    self.status_label.configure(text="Erro: Selecione uma planilha de dados de entrada.")
            except Exception:
                pass
            return

        column = self.column_entry.get().strip()
        if not column:
            try:
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    self.status_label.configure(text="Erro: Informe o nome exato da coluna com a descrição.")
            except Exception:
                pass
            return

        output_path = self._create_output_path("categorizado.xlsx")
        if not output_path:
            return

        if not self.start_execution():
            return

        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="⏳ Categorizando registros por regras de mercado...")
        except Exception:
            pass
        self.update()

        input_file = self.input_file

        theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
        visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

        def execute():
            from src.tools.categorizador.categorizador_v2 import Categorizador as Cat
            cat = Cat()
            return cat.categorize(
                input_file,
                output_path,
                description_column=column,
                category_column="categoria",
                visual_theme=visual_theme
            )

        def on_complete(result):
            self.after(0, lambda: self._on_categorize_done(result, output_path))

        g_id, g_err = task_executor.submit(
            tool_name="categorizador",
            tool_display_name="Categorizador",
            execute_func=execute,
            on_complete=on_complete,
            user_id=self.user_id,
        )
        if g_err:
            messagebox.showwarning("Aviso", g_err)

    def _on_categorize_done(self, result, output_path):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        rows = result.get("total_rows", 0)

        if result.get("success"):
            self._finalize_execution(result, output_path, rows, {"registros": rows})
            suggestions = result.get("others_suggestions", [])
            self._show_result_dashboard(result, suggestions)
            self._clear_input_file()
        else:
            self._finalize_execution(result, output_path, rows)
            from tkinter import messagebox
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="")
        except Exception:
            pass

    def _show_result_dashboard(self, result, suggestions):
        """Mostra o painel com as estatísticas, econometria de ROI e novas sugestões"""
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
        """Fecha o painel e volta para a tela de parametrização"""
        if self.result_dashboard:
            self.result_dashboard.destroy()
            self.result_dashboard = None

        self.input_section.pack(fill="both", expand=True)
        self._update_category_display()

    def _apply_suggestions(self, selected_categories):
        """Aplica na classe Categorizador as novas regras descobertas"""
        for cat_name in selected_categories:
            sug = next((s for s in self.result_dashboard.suggestions if s["category"] == cat_name), None)
            if sug:
                keywords = sug.get("keywords", [cat_name])
                self.categorizador.add_category(cat_name, keywords, priority=10)

        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="✓ Regras atualizadas com sucesso!")
        except Exception:
            pass
        self._update_category_display()
