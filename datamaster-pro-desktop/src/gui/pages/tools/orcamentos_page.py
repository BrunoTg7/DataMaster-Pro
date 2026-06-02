"""
Orçamentos Page - Preenche templates PDF em massa
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import logging
import os
import sys
import json
import pandas as pd
import threading
from datetime import datetime

log = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.orcamentos.orcamentos import Orcamentos
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


class OrcamentosPage(ToolPage):

    CAMPO_KEY_MAP = {
        "mostrar_logo": "logo",
        "mostrar_empresa": "empresa",
        "mostrar_cliente": "cliente",
        "mostrar_data": "data",
        "mostrar_itens": "itens",
        "mostrar_total": "total",
        "mostrar_validade": "validade",
        "mostrar_pagamento": "pagamento",
        "mostrar_obs": "obs",
        "mostrar_rodape": "rodape",
    }

    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.orcamentos = Orcamentos()
        self.task_helper = TaskHelper("orcamentos")
        self.execution = ExecutionHelper("orcamentos", "Orçamentos Automáticos", user_id)
        self.template_pdf = ""
        self.data_file = ""
        self.config = self._load_config()
        super().__init__(master, "orcamentos", "Orçamentos Automáticos", on_back, execution_tracker, user_id)
        self._check_task_state()

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("orcamentos")
        
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

    def _load_config(self):
        config_path = os.path.join(config.APP_DATA_DIR, "orcamentos_config.json")
        default = {
            "logo_path": "",
            "empresa_nome": "",
            "empresa_endereco": "",
            "empresa_telefone": "",
            "empresa_email": "",
            "campos_ativos": ["empresa", "cliente", "data", "itens", "total", "validade", "pagamento", "rodape"],
            "observacoes_default": "Orçamento válido por 30 dias.",
            "pdf_cor": "#d48214",
            "pdf_titulo": "ORÇAMENTO",
            "tempo_execucao_ms": 0
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    loaded_config = {**default, **json.load(f)}
            except Exception:
                loaded_config = default
        else:
            loaded_config = default
        
        # Limpar APENAS campos bloqueados (Logo e Pagamento) para FREE users
        user_data = getattr(self, 'user_data', {})
        user_plan = user_data.get("plan", "gratis").lower() if user_data else "gratis"
        if user_plan == "gratis":
            campos = loaded_config.get("campos_ativos", [])
            campos = [c for c in campos if c not in ("logo", "pagamento")]
            loaded_config["campos_ativos"] = campos
        
        return loaded_config

    def _save_config(self):
        config_path = os.path.join(config.APP_DATA_DIR, "orcamentos_config.json")
        os.makedirs(config.APP_DATA_DIR, exist_ok=True)
        
        user_data = getattr(self, 'user_data', {})
        user_plan = user_data.get("plan", "gratis").lower() if user_data else "gratis"
        config_to_save = dict(self.config)
        
        if user_plan == "gratis":
            campos = config_to_save.get("campos_ativos", [])
            campos = [c for c in campos if c not in ("logo", "pagamento")]
            config_to_save["campos_ativos"] = campos
        
        with open(config_path, "w") as f:
            json.dump(config_to_save, f, indent=2)

    def _on_config_change(self, widget_type, key, widget=None, checkbox_var=None):
        if widget_type == "entry" and widget:
            self.config[key] = widget.get()
        elif widget_type == "checkbox" and checkbox_var:
            campos = []
            for k, v in self.campo_vars.items():
                if v.get():
                    campos.append(self.CAMPO_KEY_MAP.get(k, k))
            self.config["campos_ativos"] = campos
        self._save_config()

    def _on_campos_change(self):
        campos = []
        for key, var in self.campo_vars.items():
            if var.get():
                campos.append(self.CAMPO_KEY_MAP.get(key, key))
        self.config["campos_ativos"] = campos
        self._save_config()

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)
        
        # Verificar plano do usuário NO INÍCIO para usar em todo o método
        user_plan = self.user_data.get("plan", "gratis").lower() if self.user_data else "gratis"
        is_free_user = user_plan == "gratis"

        info = ctk.CTkLabel(
            content,
            text="Gere orçamentos em PDF automaticamente a partir dos dados da planilha.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        dados_empresa_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        dados_empresa_frame.pack(fill="x", padx=20, pady=10)

        emp_title = ctk.CTkLabel(
            dados_empresa_frame,
            text="Dados da Empresa (aparecerá no orçamento)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        emp_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Aviso PRO+ para pagamento
        if is_free_user:
            payment_aviso = ctk.CTkLabel(
                dados_empresa_frame,
                text="⚠️  Dados de pagamento (PIX) disponível apenas em planos PRO e ENTERPRISE",
                font=ctk.CTkFont(size=11),
                text_color="#F59E0B"
            )
            payment_aviso.pack(anchor="w", padx=20, pady=(0, 10))

        logo_frame = ctk.CTkFrame(dados_empresa_frame, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(logo_frame, text="Logo:", width=80).pack(side="left")

        self.logo_entry = ctk.CTkEntry(logo_frame, width=250, placeholder_text="Caminho da imagem...")
        self.logo_entry.insert(0, self.config.get("logo_path", ""))
        self.logo_entry.pack(side="left", padx=10)

        self.logo_btn = ctk.CTkButton(
            logo_frame,
            text="...",
            width=40,
            command=lambda: self._select_logo(self.logo_entry)
        )
        self.logo_btn.pack(side="left")
        
        if is_free_user:
            self.logo_entry.configure(state="disabled")
            self.logo_btn.configure(state="disabled")
            aviso_logo = ctk.CTkLabel(
                logo_frame,
                text="🔒 PRO+",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#F59E0B"
            )
            aviso_logo.pack(side="left", padx=5)

        emp_fields_frame = ctk.CTkFrame(dados_empresa_frame, fg_color="transparent")
        emp_fields_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.emp_entries = {}
        emp_fields = [
            ("empresa_nome", "Nome da Empresa"),
            ("empresa_endereco", "Endereço"),
            ("empresa_telefone", "Telefone"),
            ("empresa_email", "Email")
        ]

        design_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        design_frame.pack(fill="x", padx=20, pady=10)

        design_title = ctk.CTkLabel(
            design_frame,
            text="Design do PDF",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        design_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Aviso PRO+ para recursos de design
        if is_free_user:
            pro_aviso = ctk.CTkLabel(
                design_frame,
                text="⚠️  Personalização de cor e logo disponível apenas em planos PRO e ENTERPRISE",
                font=ctk.CTkFont(size=11),
                text_color="#F59E0B"
            )
            pro_aviso.pack(anchor="w", padx=20, pady=(0, 10))

        self.design_entries = {}
        
        titulo_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        titulo_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(titulo_frame, text="Título do Orçamento:", width=100).pack(side="left")
        
        titulo_entry = ctk.CTkEntry(titulo_frame, width=200)
        titulo_entry.insert(0, self.config.get("pdf_titulo", "ORÇAMENTO"))
        titulo_entry.pack(side="left", padx=5)
        self.design_entries["pdf_titulo"] = titulo_entry
        titulo_entry.bind("<FocusOut>", lambda e: self._on_config_change("entry", "pdf_titulo", widget=titulo_entry))
        titulo_entry.bind("<Return>", lambda e: self._on_config_change("entry", "pdf_titulo", widget=titulo_entry))
        
        color_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self._selected_color = self.config.get("pdf_cor") or "#d48214"
        
        color_row = ctk.CTkFrame(color_frame, fg_color="transparent")
        color_row.pack(fill="x")
        
        ctk.CTkLabel(color_row, text="Cor Principal:").pack(side="left", padx=(0, 10))
        
        # Bloquear cor para FREE users
        if is_free_user:
            # Mostrar aviso
            aviso_cor = ctk.CTkLabel(
                color_row,
                text="🔒 PRO+ (Padrão: #d48214)",
                font=ctk.CTkFont(size=10),
                text_color="#F59E0B"
            )
            aviso_cor.pack(side="left", padx=5)
        else:
            self.color_btn = ctk.CTkButton(
                color_row,
                text="Escolher",
                width=80,
                height=30,
                fg_color=self._selected_color if self._selected_color != "#d48214" else config.Colors.PRIMARY,
                command=self._choose_color
            )
            self.color_btn.pack(side="left", padx=5)
            
            self.color_label = ctk.CTkLabel(
                color_row,
                text=self._selected_color,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=config.Colors.PRIMARY
            )
            self.color_label.pack(side="left", padx=5)
            
            ctk.CTkButton(
                color_row,
                text="Padrão",
                width=70,
                height=30,
                fg_color="#d48214",
                border_width=1,
                border_color=config.Colors.BORDER,
                command=self._reset_color
            ).pack(side="left", padx=10)

        campos_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        campos_frame.pack(fill="x", padx=20, pady=(0, 15))

        campos_label_frame = ctk.CTkFrame(campos_frame, fg_color="transparent")
        campos_label_frame.pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(campos_label_frame, text="Campos no PDF:").pack(anchor="w", side="left")

        self.campo_vars = {}
        campos_check = [
            ("mostrar_logo", "Logo"),
            ("mostrar_empresa", "Dados da Empresa"),
            ("mostrar_cliente", "Dados do Cliente"),
            ("mostrar_data", "Data"),
            ("mostrar_itens", "Tabela de Itens"),
            ("mostrar_total", "Total Geral"),
            ("mostrar_validade", "Validade"),
            ("mostrar_pagamento", "Pagamento"),
            ("mostrar_obs", "Observações"),
            ("mostrar_rodape", "Rodapé")
        ]

        campos_ativos = self.config.get("campos_ativos", [])
        
        checkbox_frame = ctk.CTkFrame(campos_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x")
        checkbox_frame.grid_columnconfigure(0, weight=1)
        checkbox_frame.grid_columnconfigure(1, weight=1)
        
        # Campos bloqueados para FREE users
        campos_bloqueados_free = ["mostrar_logo", "mostrar_pagamento"]
        
        for i, (key, label) in enumerate(campos_check):
            row = i // 2
            col = i % 2
            campo_name = self.CAMPO_KEY_MAP.get(key, key)
            var = ctk.CTkCheckBox(checkbox_frame, text=label, command=self._on_campos_change)
            if campo_name in campos_ativos:
                var.select()
            var.grid(row=row, column=col, sticky="w", padx=10, pady=2)
            
            # Desabilitar apenas Logo e Pagamento para FREE users
            if is_free_user and key in campos_bloqueados_free:
                var.configure(state="disabled")
                # Adicionar badge de bloqueio visual
                aviso_campo = ctk.CTkLabel(
                    checkbox_frame,
                    text="🔒",
                    font=ctk.CTkFont(size=9),
                    text_color="#F59E0B"
                )
                aviso_campo.grid(row=row, column=col, sticky="e", padx=(0, 10))
            
            self.campo_vars[key] = var

        def format_phone(value):
            digits = "".join(c for c in value if c.isdigit())[:11]
            if len(digits) <= 2:
                return f"({digits}" if digits else ""
            elif len(digits) <= 7:
                return f"({digits[:2]}){digits[2:]}"
            else:
                return f"({digits[:2]}){digits[2:7]}-{digits[7:]}"

        def on_phone_keyrelease(event, entry):
            raw = entry.get()
            formatted = format_phone(raw)
            entry.delete(0, "end")
            entry.insert(0, formatted)
            entry.icursor("end")

        for i, (key, label) in enumerate(emp_fields):
            row = i // 2
            col = (i % 2) * 2
            
            ctk.CTkLabel(emp_fields_frame, text=f"{label}:", width=100).grid(row=row, column=col, sticky="w", padx=5, pady=3)

            width = 150 if key == "empresa_telefone" else 200
            entry = ctk.CTkEntry(emp_fields_frame, width=width)
            entry.insert(0, self.config.get(key, ""))
            entry.grid(row=row, column=col+1, padx=5, pady=3)
            self.emp_entries[key] = entry

            if key == "empresa_telefone":
                entry.bind("<KeyRelease>", lambda e, w=entry: on_phone_keyrelease(e, w))

            entry.bind("<FocusOut>", lambda e, k=key, w=entry: self._on_config_change("entry", k, widget=w))
            entry.bind("<Return>", lambda e, k=key, w=entry: self._on_config_change("entry", k, widget=w))

       
        obs_frame = ctk.CTkFrame(dados_empresa_frame, fg_color="transparent")
        obs_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(obs_frame, text="Observações (cada linha = uma obs no PDF):").pack(anchor="w", padx=10, pady=(0, 5))

        # Definimos um width fixo (ex: 300). Ele não vai esticar até o fim da tela.
        self.obs_textbox = ctk.CTkTextbox(obs_frame, width=550, height=80)
        self.obs_textbox.insert("1.0", self.config.get("observacoes_default", ""))

        # Usamos apenas anchor="w" para ele ficar alinhado à esquerda e não crescer
        self.obs_textbox.pack(anchor="w", padx=10, pady=5)

        pix_frame = ctk.CTkFrame(dados_empresa_frame, fg_color="transparent")
        pix_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        pix_title_frame = ctk.CTkFrame(pix_frame, fg_color="transparent")
        pix_title_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(pix_title_frame, text="Dados para Pagamento (PIX):").pack(anchor="w", side="left")
        
        if is_free_user:
            aviso_pix = ctk.CTkLabel(
                pix_title_frame,
                text="🔒 PRO+",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#F59E0B"
            )
            aviso_pix.pack(side="left", padx=5)
        
        pix_grid_frame = ctk.CTkFrame(pix_frame, fg_color="transparent")
        pix_grid_frame.pack(fill="x")
        
        pix_fields = [
            ("pix_chave", "Chave PIX"),
            ("banco", "Banco"),
            ("agencia", "Agência"),
            ("conta", "Conta")
        ]
        
        for i, (key, label) in enumerate(pix_fields):
            row = i // 2
            col = (i % 2) * 2
            ctk.CTkLabel(pix_grid_frame, text=f"{label}:", width=80).grid(row=row, column=col, sticky="w", padx=5, pady=2)
            entry = ctk.CTkEntry(pix_grid_frame, width=180)
            entry.insert(0, self.config.get(key, ""))
            entry.grid(row=row, column=col+1, padx=5, pady=2)
            self.emp_entries[key] = entry
            
            # Desabilitar entrada para FREE users
            if is_free_user:
                entry.configure(state="disabled")
            
            entry.bind("<FocusOut>", lambda e, k=key, w=entry: self._on_config_change("entry", k, widget=w))
            entry.bind("<Return>", lambda e, k=key, w=entry: self._on_config_change("entry", k, widget=w))

        self.data_drop = self._create_drop_zone(
            content,
            "2. Arraste a Base de Dados (Excel/CSV)",
            self._select_data
        )

        self.data_file_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.data_file_frame.pack(pady=(0, 5))

        self.data_label = ctk.CTkLabel(
            self.data_file_frame,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.data_label.pack(side="left")

        self.data_clear_btn = ctk.CTkButton(
            self.data_file_frame,
            text="✕",
            width=24,
            height=20,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent",
            hover_color="#e74c3c",
            text_color="#a0a0a0",
            corner_radius=3,
            command=self._clear_data_file
        )
        self.data_clear_btn.pack(side="left", padx=(6, 0))
        self.data_clear_btn.pack_forget()

        self.action_btn = self._create_action_button(content, "Gerar Orçamentos", self._run_generate)

        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)

    def _select_template(self, files=None):
        if files:
            self.template_pdf = files[0]
            self.template_label.configure(text=f"✓ {os.path.basename(self.template_pdf)}")
            fields = self.orcamentos.get_template_fields(self.template_pdf)
            if fields:
                self.template_label.configure(
                    text=f"✓ {os.path.basename(self.template_pdf)} ({len(fields)} campos)"
                )
        else:
            files = self._browse_files([("PDF", "*.pdf")])
            if files:
                self.template_pdf = files[0]
                self.template_label.configure(text=f"✓ {os.path.basename(self.template_pdf)}")
                fields = self.orcamentos.get_template_fields(self.template_pdf)
                if fields:
                    self.template_label.configure(
                        text=f"✓ {os.path.basename(self.template_pdf)} ({len(fields)} campos)"
                    )

    def _clear_data_file(self):
        self.data_file = ""
        self.data_label.configure(text="Nenhum arquivo selecionado")
        self.data_clear_btn.pack_forget()

    def _select_data(self, files=None):
        if files:
            self.data_file = files[0]
            self.data_label.configure(text=f"✓ {os.path.basename(self.data_file)}")
            self.data_clear_btn.pack(side="left", padx=(6, 0))
        else:
            files = self._browse_files([
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv")
            ])
            if files:
                self.data_file = files[0]
                self.data_label.configure(text=f"✓ {os.path.basename(self.data_file)}")
                self.data_clear_btn.pack(side="left", padx=(6, 0))

    def _select_logo(self, entry):
        files = filedialog.askopenfilenames(title="Selecionar Logo", filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if files:
            entry.delete(0, "end")
            entry.insert(0, files[0])
            self.config["logo_path"] = files[0]
            self._save_config()
    
    def _choose_color(self):
        from tkinter import colorchooser
        color_code = colorchooser.askcolor(title="Escolha a cor", color=self._selected_color)
        if color_code and color_code[1] and color_code[1].strip():
            self._selected_color = color_code[1]
            self.color_btn.configure(fg_color=self._selected_color)
            self.color_label.configure(text=self._selected_color)
            self.config["pdf_cor"] = self._selected_color
            self._save_config()
    
    def _reset_color(self):
        self._selected_color = "#d48214"
        self.color_btn.configure(fg_color=self._selected_color)
        self.color_label.configure(text=self._selected_color)
        self.config["pdf_cor"] = self._selected_color
        self._save_config()

    def _run_generate(self):
        log.debug("_run_generate iniciado")
        
        user_plan = self.user_data.get("plan", "gratis").lower() if self.user_data else "gratis"
        is_free_user = user_plan == "gratis"
        
        for key, entry in self.emp_entries.items():
            self.config[key] = entry.get()
        
        self.config["logo_path"] = self.logo_entry.get()
        self.config["observacoes_default"] = self.obs_textbox.get("1.0", "end").strip()
        
        self.config["pdf_titulo"] = self.design_entries["pdf_titulo"].get()
        self.config["pdf_cor"] = self._selected_color
        
        # Construir campos_ativos com nomes curtos, forçando logo/pagamento off para FREE
        campos = []
        for key, var in self.campo_vars.items():
            campo_name = self.CAMPO_KEY_MAP.get(key, key)
            if var.get():
                if is_free_user and campo_name in ("logo", "pagamento"):
                    continue
                campos.append(campo_name)
        self.config["campos_ativos"] = campos
        
        self._save_config()
        
        log.debug("data_file: %s", self.data_file)
        
        if not self.data_file:
            messagebox.showwarning("Aviso", "Selecione um arquivo de dados primeiro")
            return

        output_dir = filedialog.askdirectory(title="Selecione diretório para salvar os PDFs")
        log.debug("output_dir: %s", output_dir)
        
        if not output_dir:
            log.debug("Nenhum diretório selecionado")
            return

        has_watermark = is_free_user
        
        log.debug("user_plan: %s, watermark: %s", user_plan, has_watermark)
        
        log.debug("Lendo arquivo Excel...")
        
        import time
        start_time = time.time()
        
        try:
            df = pd.read_excel(self.data_file)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")
            return
        
        log.debug("Linhas lidas: %d", len(df))
        
        def get_nome_cliente(row):
            for col in row.index:
                if "nome" in str(col).lower() and "cliente" in str(col).lower():
                    return str(row[col]).strip().lower()
            return None
        
        unique_clientes = set()
        for idx, row in df.iterrows():
            nome = get_nome_cliente(row)
            if nome and nome not in ["nan", "none", "null", ""]:
                unique_clientes.add(nome)
        
        total_docs = len(unique_clientes)
        log.debug("Clientes únicos: %d", total_docs)
        
        if user_plan.upper() == "GRATIS":
            log.debug("Verificando limites...")
            from src.core.sync.sync_manager import ExecutionTracker
            tracker = self.execution_tracker
            log.debug("tracker: %s, user_id: %s", tracker, self.user_id)
            if tracker and self.user_id:
                stats = tracker.get_user_stats(self.user_id)
                log.debug("stats: %s", stats)
                tool_stats = stats.get("by_tool", {}).get("orcamentos", {"execs": 0, "lines": 0})
                current_execs = tool_stats.get("execs", 0)
                current_docs = tool_stats.get("lines", 0)
                
                max_execs = 5
                max_docs = 15
                
                if current_execs >= max_execs:
                    log.debug("Limite execucoes atingido: %d/%d", current_execs, max_execs)
                    try:
                        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                            self.status_label.configure(text=f"Limite de {max_execs} execuções atingido. Upgrade para PRO!")
                    except Exception:
                        pass
                    self.update()
                    messagebox.showwarning("Limite Atingido", f"Você já usou {current_execs} execuções. O limite é {max_execs} por mês. Upgrade para PRO!")
                    return
                    
                remaining_docs = max_docs - current_docs
                log.debug("Limite check: %d usados, %d planejamento, %d restantes", current_docs, total_docs, remaining_docs)
                
                if remaining_docs <= 0:
                    log.debug("Limite docs atingido: %d/%d", current_docs, max_docs)
                    try:
                        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                            self.status_label.configure(text=f"Limite de {max_docs} documentos atingido. Upgrade para PRO!")
                    except Exception:
                        pass
                    self.update()
                    messagebox.showwarning("Limite Atingido", f"Você já gerou {current_docs} documentos. O limite é {max_docs}. Upgrade para PRO!")
                    return
                    
                if total_docs > remaining_docs:
                    self.config["limite_docs"] = remaining_docs
                    log.debug("Limitando a %d documentos (requested %d)", remaining_docs, total_docs)
                else:
                    if "limite_docs" in self.config:
                        del self.config["limite_docs"]
                    log.debug("Sem limite - gerando até %d documentos", total_docs)
                    
                log.debug("Limit check: %d/%d execs, %d/%d docs", current_execs, max_execs, current_docs, max_docs)
            
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="Processando...")
        except Exception:
            pass
        self.update()

        log.debug("Chamando generate_from_excel com config: %s", self.config)

        cfg = dict(self.config)

        def execute():
            log.debug("execute() started in thread")
            from src.tools.orcamentos.orcamentos import Orcamentos as Orc
            o = Orc()
            result = o.generate_from_excel(self.data_file, output_dir, watermark=has_watermark, config=cfg)
            result["rows_processed"] = result.get("generated", 0)
            result["output_path"] = result.get("output_dir", "")
            log.debug("execute() done: %s PDFs", result.get('generated'))
            return result

        def on_complete(result):
            self.after(0, lambda: self._on_orcamentos_done(result, output_dir))

        g_id, g_err = task_executor.submit(
            tool_name="orcamentos",
            tool_display_name="Orçamentos",
            execute_func=execute,
            on_complete=on_complete,
            user_id=self.user_id,
        )
        if g_err:
            messagebox.showwarning("Aviso", g_err)
            return

        self.execution.task_id = g_id

    def _on_orcamentos_done(self, result, output_dir):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        generated = result.get("generated", 0)

        if result.get("success"):
            import glob, zipfile
            pdfs = glob.glob(os.path.join(output_dir, "*.pdf"))
            if pdfs:
                try:
                    zip_name = f"orcamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                    zip_path = os.path.join(output_dir, zip_name)
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for pdf in pdfs:
                            zf.write(pdf, os.path.basename(pdf))
                    for pdf in pdfs:
                        try:
                            os.remove(pdf)
                        except Exception:
                            pass
                    generated_files = [zip_path]
                except Exception as e:
                    log.error("Erro ao criar zip: %s", e)
                    generated_files = pdfs
                self._finalize_execution(result, output_dir, generated,
                                         {"pdfs_gerados": generated},
                                         generated_files=generated_files)
            else:
                self._finalize_execution(result, "", generated)
        else:
            self._finalize_execution(result, "", 0)

        try:
            if self.winfo_exists():
                self.status_label.configure(
                    text=f"✅ {generated} orçamento(s) gerado(s) com sucesso!" if result.get("success")
                    else f"❌ Erro: {result.get('error', 'Desconhecido')}"
                )
                if result.get("success"):
                    self._clear_data_file()
        except Exception:
            pass
        log.debug("_on_orcamentos_done finished")

