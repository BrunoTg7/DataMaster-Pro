"""
Orçamentos Page - Preenche templates PDF em massa
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import json
import pandas as pd
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.orcamentos.orcamentos import Orcamentos
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.global_executor import global_executor


class OrcamentosPage(ToolPage):
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
        from src.core.storage.storage_manager import StorageManager
        storage = StorageManager()
        last_task = storage.get_last_task_by_tool("orcamentos")
        
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
                    return {**default, **json.load(f)}
            except Exception:
                return default
        return default

    def _save_config(self):
        config_path = os.path.join(config.APP_DATA_DIR, "orcamentos_config.json")
        os.makedirs(config.APP_DATA_DIR, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def _on_config_change(self, widget_type, key, widget=None, checkbox_var=None):
        if widget_type == "entry" and widget:
            self.config[key] = widget.get()
        elif widget_type == "checkbox" and checkbox_var:
            campos = []
            for k, v in self.campo_vars.items():
                if v.get():
                    campos.append(k)
            self.config["campos_ativos"] = campos
        self._save_config()

    def _on_campos_change(self):
        campos = []
        for key, var in self.campo_vars.items():
            if var.get():
                campos.append(key)
        self.config["campos_ativos"] = campos
        self._save_config()

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

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

        logo_frame = ctk.CTkFrame(dados_empresa_frame, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(logo_frame, text="Logo:", width=80).pack(side="left")

        self.logo_entry = ctk.CTkEntry(logo_frame, width=250, placeholder_text="Caminho da imagem...")
        self.logo_entry.insert(0, self.config.get("logo_path", ""))
        self.logo_entry.pack(side="left", padx=10)

        ctk.CTkButton(
            logo_frame,
            text="...",
            width=40,
            command=lambda: self._select_logo(self.logo_entry)
        ).pack(side="left")

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

        ctk.CTkLabel(campos_frame, text="Campos no PDF:").pack(anchor="w", pady=(0, 5))

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
        
        for i, (key, label) in enumerate(campos_check):
            row = i // 2
            col = i % 2
            var = ctk.CTkCheckBox(checkbox_frame, text=label, command=self._on_campos_change)
            if key in campos_ativos or key not in ["mostrar_logo", "mostrar_empresa"]:
                var.select()
            var.grid(row=row, column=col, sticky="w", padx=10, pady=2)
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
        
        ctk.CTkLabel(pix_frame, text="Dados para Pagamento (PIX):").pack(anchor="w", pady=(0, 5))
        
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
            entry.bind("<FocusOut>", lambda e, k=key, w=entry: self._on_config_change("entry", k, widget=w))
            entry.bind("<Return>", lambda e, k=key, w=entry: self._on_config_change("entry", k, widget=w))

        self.data_drop = self._create_drop_zone(
            content,
            "2. Arraste a Base de Dados (Excel/CSV)",
            self._select_data
        )

        self.data_label = ctk.CTkLabel(
            content,
            text="Nenhum arquivo selecionado",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.data_label.pack(pady=(0, 5))

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

    def _select_data(self, files=None):
        if files:
            self.data_file = files[0]
            self.data_label.configure(text=f"✓ {os.path.basename(self.data_file)}")
        else:
            files = self._browse_files([
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv")
            ])
            if files:
                self.data_file = files[0]
                self.data_label.configure(text=f"✓ {os.path.basename(self.data_file)}")

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
        print("[DEBUG] _run_generate iniciado")
        
        # Criar task no ExecutionManager (para histórico)
        task_id, err = self.execution.create_task()
        print(f"[DEBUG] create_task result: task_id={task_id}, err={err}")
        if err:
            print(f"[DEBUG] create_task error: {err}")
            messagebox.showwarning("Aviso", err)
            return
        
        for key, entry in self.emp_entries.items():
            self.config[key] = entry.get()
        self.config["logo_path"] = self.logo_entry.get()
        self.config["observacoes_default"] = self.obs_textbox.get("1.0", "end").strip()
        
        self.config["pdf_titulo"] = self.design_entries["pdf_titulo"].get()
        self.config["pdf_cor"] = self._selected_color
        
        campos = []
        for key, var in self.campo_vars.items():
            if var.get():
                campos.append(key)
        self.config["campos_ativos"] = campos
        
        self._save_config()
        
        print(f"[DEBUG] data_file: {self.data_file}")
        
        if not self.data_file:
            messagebox.showwarning("Aviso", "Selecione um arquivo de dados primeiro")
            return

        output_dir = filedialog.askdirectory(title="Selecione diretório para salvar os PDFs")
        print(f"[DEBUG] output_dir: {output_dir}")
        
        if not output_dir:
            print("[DEBUG] Nenhum diretório selecionado")
            return

        user_plan = self.user_data.get("plan", "gratis") if self.user_data else "gratis"
        has_watermark = user_plan.upper() == "GRATIS"
        
        print(f"[DEBUG] user_plan: {user_plan}, watermark: {has_watermark}")
        
        print("[DEBUG] Lendo arquivo Excel...")
        
        import time
        start_time = time.time()
        
        try:
            df = pd.read_excel(self.data_file)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")
            return
        
        print(f"[DEBUG] Linhas lidas: {len(df)}")
        
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
        print(f"[DEBUG] Clientes únicos: {total_docs}")
        
        if user_plan.upper() == "GRATIS":
            print("[DEBUG] Verificando limites...")
            from src.core.sync.sync_manager import ExecutionTracker
            tracker = self.execution_tracker
            print(f"[DEBUG] tracker: {tracker}, user_id: {self.user_id}")
            if tracker and self.user_id:
                stats = tracker.get_user_stats(self.user_id)
                print(f"[DEBUG] stats: {stats}")
                tool_stats = stats.get("by_tool", {}).get("orcamentos", {"execs": 0, "lines": 0})
                current_execs = tool_stats.get("execs", 0)
                current_docs = tool_stats.get("lines", 0)
                
                max_execs = 5
                max_docs = 15
                
                if current_execs >= max_execs:
                    print(f"[DEBUG] Limite execucoes atingido: {current_execs}/{max_execs}")
                    try:
                        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                            self.status_label.configure(text=f"Limite de {max_execs} execuções atingido. Upgrade para PRO!")
                    except Exception:
                        pass
                    self.update()
                    messagebox.showwarning("Limite Atingido", f"Você já usou {current_execs} execuções. O limite é {max_execs} por mês. Upgrade para PRO!")
                    return
                    
                remaining_docs = max_docs - current_docs
                print(f"[DEBUG] Limite check: {current_docs} usados, {total_docs} planejamento, {remaining_docs} restantes")
                
                if remaining_docs <= 0:
                    print(f"[DEBUG] Limite docs atingido: {current_docs}/{max_docs}")
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
                    print(f"[DEBUG] Limitando a {remaining_docs} documentos (requested {total_docs})")
                else:
                    if "limite_docs" in self.config:
                        del self.config["limite_docs"]
                    print(f"[DEBUG] Sem limite - gerando até {total_docs} documentos")
                    
                print(f"[DEBUG] Limit check: {current_execs}/{max_execs} execs, {current_docs}/{max_docs} docs")
            
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text="Processando...")
        except Exception:
            pass
        self.update()

        print(f"[DEBUG] Chamando generate_from_excel com config: {self.config}")

        data_file = self.data_file
        cfg = dict(self.config)
        self._exec_result = None
        self._exec_data = {"output_dir": output_dir, "start_time": start_time}

        def execute():
            print("[DEBUG] execute() started in thread")
            from src.tools.orcamentos.orcamentos import Orcamentos as Orc
            o = Orc()
            result = o.generate_from_excel(data_file, output_dir, watermark=has_watermark, config=cfg)
            result["rows_processed"] = result.get("generated", 0)
            result["output_path"] = result.get("output_dir", "")
            print(f"[DEBUG] execute() done: {result.get('generated')} PDFs")
            return result

        g_id, g_err = global_executor.submit(
            tool_name="orcamentos",
            tool_display_name="Orçamentos",
            execute_func=execute,
            on_complete=lambda r: setattr(self, '_exec_result', r),
            user_id=self.user_id,
        )
        if g_err:
            messagebox.showwarning("Aviso", g_err)
            return

        self._poll_task_completion()

    def _poll_task_completion(self):
        if not hasattr(self, '_exec_result') or self._exec_result is None:
            self.after(500, self._poll_task_completion)
            return
        result = self._exec_result
        self._on_orcamentos_done(result, self._exec_data["output_dir"], self._exec_data["start_time"])
        self._exec_result = None
        self._exec_data = None

    def _on_orcamentos_done(self, result, output_dir, start_time):
        print(f"[DEBUG] _on_orcamentos_done called: success={result.get('success')}, generated={result.get('generated', 0)}")

        import time
        generated = result.get("generated", 0)
        status = "completed" if result.get("success") and generated > 0 else "failed"

        tempo_ms = int((time.time() - start_time) * 1000)

        # Persist execution data even if page is gone
        try:
            self.config["tempo_execucao_ms"] = tempo_ms
            self._save_config()
        except Exception:
            pass

        if result.get("success"):
            # Backup dos PDFs gerados
            import glob, shutil
            from pathlib import Path
            pdfs = glob.glob(os.path.join(output_dir, "*.pdf"))
            if pdfs:
                # Usa o _finalize_execution que já faz backup + histórico
                # Para múltiplos PDFs, criamos um único output_path apontando para o diretório
                self._finalize_execution(result, output_dir, generated,
                                         {"pdfs_gerados": generated})
            else:
                self._finalize_execution(result, "", generated)
        else:
            self._finalize_execution(result, "", 0)

        # UI updates only if page still exists
        try:
            if self.winfo_exists():
                self.status_label.configure(
                    text=f"✅ {generated} orçamento(s) gerado(s) com sucesso!" if result.get("success")
                    else f"❌ Erro: {result.get('error', 'Desconhecido')}"
                )

                if result.get("success"):
                    self.data_file = ""
                    self.data_label.configure(text="Nenhum arquivo selecionado")
        except Exception:
            pass
        print("[DEBUG] _on_orcamentos_done finished")

