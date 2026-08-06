"""
Gerador de Laudos de Conformidade Enterprise v3.0
Template Engine Jinja2 + WeasyPrint + Assinatura Digital ICP-Brasil
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.gerador_laudos import GeradorLaudosEnterprise, LaudoConfig
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


class GeradorLaudosPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.laudos = GeradorLaudosEnterprise(log_callback=self._log_msg)
        self.template_engine = TemplateEngine()
        self.execution = ExecutionHelper("gerador_laudos", "Gerador de Laudos Enterprise", user_id)
        super().__init__(master, "gerador_laudos", "Gerador de Laudos Enterprise v3.0", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.extrato_file = None
        self.notas_file = None
        self._last_result_text = ""
        self._check_template_status()

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("gerador_laudos")
        
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
            text=(
                "Gerador de Laudos Enterprise v3.0\n"
                "✅ Template Engine Jinja2  |  ✅ WeasyPrint (CSS Paged Media)  |  ✅ Assinatura Digital ICP-Brasil  |  ✅ Auditoria SHA-256"
            ),
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=550,
            justify="left"
        )
        info.pack(pady=(20, 10))

        # ── Templates disponíveis ──────────────────────────────────────
        self.available_templates = self.laudos.get_available_templates()
        
        template_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        template_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            template_frame,
            text="🎨 Template do Laudo:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 5))

        template_options = [t.replace("_", " ").title() for t in self.available_templates]
        self.template_menu = ctk.CTkOptionMenu(
            template_frame,
            values=template_options,
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER
        )
        self.template_menu.set(template_options[0] if template_options else "Default")
        self.template_menu.pack(anchor="w", padx=20, pady=(0, 15))

        # ── Arquivos de entrada ────────────────────────────────────────
        input_frame = ctk.CTkFrame(self, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            input_frame,
            text="📁 Arquivos de Entrada:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 5))

        # Extrato
        extrato_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        extrato_row.pack(fill="x", padx=20, pady=(5, 10))
        ctk.CTkLabel(extrato_row, text="📄 Extrato Bancário:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 10))
        self.extrato_label = ctk.CTkLabel(extrato_row, text="Nenhum arquivo", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY)
        self.extrato_label.pack(side="left", padx=(0, 10))
        ctk.CTkButton(extrato_row, text="Selecionar Extrato", command=self._select_extrato, fg_color=config.Colors.PRIMARY, width=150).pack(side="left", padx=5)
        self.extrato_clear_btn = ctk.CTkButton(extrato_row, text="✕", width=24, height=20, font=ctk.CTkFont(size=10, weight="bold"), fg_color="transparent", hover_color="#e74c3c", text_color="#a0a0a0", corner_radius=3, command=self._clear_extrato)
        self.extrato_clear_btn.pack(side="left", padx=5)
        self.extrato_clear_btn.pack_forget()

        # Notas
        notas_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        notas_row.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(notas_row, text="📋 Notas Fiscais:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 10))
        self.notas_label = ctk.CTkLabel(notas_row, text="Nenhum arquivo", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY)
        self.notas_label.pack(side="left", padx=(0, 10))
        ctk.CTkButton(notas_row, text="Selecionar Notas", command=self._select_notas, fg_color=config.Colors.PRIMARY, width=150).pack(side="left", padx=5)
        self.notas_clear_btn = ctk.CTkButton(notas_row, text="✕", width=24, height=20, font=ctk.CTkFont(size=10, weight="bold"), fg_color="transparent", hover_color="#e74c3c", text_color="#a0a0a0", corner_radius=3, command=self._clear_notas)
        self.notas_clear_btn.pack(side="left", padx=5)
        self.notas_clear_btn.pack_forget()

        # ── Configurações Avançadas ────────────────────────────────────
        config_frame = ctk.CTkFrame(self, fg_color=config.Colors.CARD, corner_radius=12)
        config_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(config_frame, text="⚙️ Configurações do Laudo:", font=ctk.CTkFont(size=13, weight="bold"), text_color=config.Colors.TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 10))

        # Grid de configurações
        grid = ctk.CTkFrame(config_frame, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 15))
        grid.grid_columnconfigure(1, weight=1)

        # Linha 1: Empresa + CNPJ
        ctk.CTkLabel(grid, text="Empresa:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=4)
        self.company_entry = ctk.CTkEntry(grid, placeholder_text="Ex: Minha Empresa Ltda", font=ctk.CTkFont(size=11))
        self.company_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        ctk.CTkLabel(grid, text="CNPJ:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).grid(row=1, column=0, sticky="w", pady=4)
        self.cnpj_entry = ctk.CTkEntry(grid, placeholder_text="00.000.000/0001-00", width=200, font=ctk.CTkFont(size=11))
        self.cnpj_entry.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)

        # Linha 2: Endereço + Tolerância
        ctk.CTkLabel(grid, text="Endereço:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).grid(row=2, column=0, sticky="w", pady=4)
        self.address_entry = ctk.CTkEntry(grid, placeholder_text="Rua Exemplo, 123 - Cidade - UF", font=ctk.CTkFont(size=11))
        self.address_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=4)

        ctk.CTkLabel(grid, text="Tolerância (R$):", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).grid(row=3, column=0, sticky="w", pady=4)
        self.tolerance_entry = ctk.CTkEntry(grid, placeholder_text="1.00", width=100, font=ctk.CTkFont(size=11))
        self.tolerance_entry.insert(0, "1.00")
        self.tolerance_entry.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=4)

        # Linha 3: Rodapé + Template
        ctk.CTkLabel(grid, text="Rodapé:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).grid(row=4, column=0, sticky="w", pady=4)
        self.footer_entry = ctk.CTkEntry(grid, placeholder_text="Documento gerado automaticamente por DataMaster Pro", font=ctk.CTkFont(size=11))
        self.footer_entry.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=4)

        # ── Assinatura Digital ICP-Brasil ──────────────────────────────
        sign_frame = ctk.CTkFrame(config_frame, fg_color=config.Colors.BACKGROUND, corner_radius=8)
        sign_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.sign_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(sign_frame, text="🔏 Assinatura Digital ICP-Brasil (pAdES)", variable=self.sign_enabled_var, font=ctk.CTkFont(size=11, weight="bold"), text_color=config.Colors.TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))

        self.sign_frame = ctk.CTkFrame(sign_frame, fg_color="transparent")
        self.sign_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.sign_frame.pack_forget()

        def toggle_sign(*args):
            if self.sign_enabled_var.get():
                self.sign_frame.pack(fill="x", padx=15, pady=(0, 10))
            else:
                self.sign_frame.pack_forget()
        self.sign_enabled_var.trace_add("write", toggle_sign)

        # Certificado PFX
        pfx_row = ctk.CTkFrame(self.sign_frame, fg_color="transparent")
        pfx_row.pack(fill="x", pady=5)
        ctk.CTkLabel(pfx_row, text="Certificado .pfx:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 10))
        self.cert_path_entry = ctk.CTkEntry(pfx_row, placeholder_text="Caminho do certificado .pfx", font=ctk.CTkFont(size=11))
        self.cert_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(pfx_row, text="Procurar", width=80, command=self._select_cert).pack(side="left")

        # Senha
        pwd_row = ctk.CTkFrame(self.sign_frame, fg_color="transparent")
        pwd_row.pack(fill="x", pady=5)
        ctk.CTkLabel(pwd_row, text="Senha:", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 10))
        self.cert_password_entry = ctk.CTkEntry(pwd_row, placeholder_text="Senha do certificado", show="•", width=200, font=ctk.CTkFont(size=11))
        self.cert_password_entry.pack(side="left")

        # Alias (opcional)
        alias_row = ctk.CTkFrame(self.sign_frame, fg_color="transparent")
        alias_row.pack(fill="x", pady=(5, 10))
        ctk.CTkLabel(alias_row, text="Alias (opcional):", font=ctk.CTkFont(size=11), text_color=config.Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 10))
        self.cert_alias_entry = ctk.CTkEntry(alias_row, placeholder_text="Alias do certificado", width=200, font=ctk.CTkFont(size=11))
        self.cert_alias_entry.pack(side="left")

        # ── Botão de Ação ──────────────────────────────────────────────
        self.action_btn = self._create_action_button(self, "📄 Gerar Laudo PDF Enterprise", self._run_generation)

        # ── Resultado ──────────────────────────────────────────────────
        results_label = ctk.CTkLabel(self, text="Resultado:", font=ctk.CTkFont(size=14, weight="bold"), text_color=config.Colors.TEXT_PRIMARY)
        results_label.pack(anchor="w", padx=20, pady=(15, 5))

        self.results_frame = ctk.CTkFrame(self, fg_color=config.Colors.CARD, corner_radius=12)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.results_text = ctk.CTkTextbox(self.results_frame, width=500, height=250, font=ctk.CTkFont(family="Consolas", size=11))
        self.results_text.pack(padx=20, pady=20, fill="both", expand=True)
        self.results_text.insert("1.0", "Configure o laudo e clique em gerar...\n")
        self.results_text.configure(state="disabled")

        self.viewer_btn = ResultViewerButton(self, self, lambda: self._last_result_text if hasattr(self, '_last_result_text') else "", "👁️ Visualizar Laudo")
        self.viewer_btn.pack(pady=(0, 15))

    def _check_template_status(self):
        """Verifica templates disponíveis e atualiza UI"""
        try:
            templates = self.laudos.get_available_templates()
            self.available_templates = templates
            if hasattr(self, 'template_menu') and self.template_menu.winfo_exists():
                options = [t.replace("_", " ").title() for t in templates]
                self.template_menu.configure(values=options)
                if options:
                    self.template_menu.set(options[0])
            self._log_msg(f"> Templates disponíveis: {', '.join(templates) if templates else 'Nenhum'}")
        except Exception as e:
            self._log_msg(f"> Erro ao carregar templates: {e}")

    def _log_msg(self, msg: str):
        self.after(0, lambda: self._update_results_text(f"> {msg}\n"))

    def _update_results_text(self, text: str):
        try:
            if hasattr(self, 'results_text') and self.results_text.winfo_exists():
                self.results_text.configure(state="normal")
                self.results_text.insert("end", text)
                self.results_text.see("end")
                self.results_text.configure(state="disabled")
        except Exception:
            pass
        self.extrato_file = None
        self.extrato_label.configure(text="")
        self.extrato_clear_btn.pack_forget()
        self._update_status()

    def _clear_notas(self):
        self.notas_file = None
        self.notas_label.configure(text="")
        self.notas_clear_btn.pack_forget()
        self._update_status()

    def _select_extrato(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar Extrato",
            filetypes=[
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Todos", "*.*")
            ]
        )
        
        if file_path:
            self.extrato_file = file_path
            self.extrato_label.configure(text=os.path.basename(file_path))
            self.extrato_clear_btn.pack(side="left", padx=(6, 0))
            self._update_status()

    def _select_notas(self):
        file_path = filedialog.askopenfilename(
            title="Selecionar Notas Fiscais",
            filetypes=[
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Todos", "*.*")
            ]
        )
        
        if file_path:
            self.notas_file = file_path
            self.notas_label.configure(text=os.path.basename(file_path))
            self.notas_clear_btn.pack(side="left", padx=(6, 0))
            self._update_status()

    def _update_status(self):
        status_text = ""
        if self.extrato_file:
            status_text += f"Extrato: {os.path.basename(self.extrato_file)}\n"
        if self.notas_file:
            status_text += f"Notas: {os.path.basename(self.notas_file)}\n"

        if status_text:
            try:
                if hasattr(self, 'results_text') and self.results_text.winfo_exists():
                    self.results_text.configure(state="normal")
                    self.results_text.delete("1.0", "end")
                    self.results_text.insert("1.0", status_text + "\nPronto para gerar!")
                    self.results_text.configure(state="disabled")
            except Exception:
                pass

    def _run_generation(self):
        if not self.extrato_file:
            messagebox.showwarning("Aviso", "Selecione o extrato bancário")
            return
        
        if not self.notas_file:
            messagebox.showwarning("Aviso", "Selecione o arquivo de notas fiscais")
            return

        output_path = filedialog.asksaveasfilename(
            title="Salvar Laudo",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        
        if not output_path:
            return

        # Mapear template selecionado para nome interno
        template_map = {
            "Default": "default",
            "Minimal": "minimal",
            "Executivo": "executivo"
        }
        selected_template = self.template_menu.get()
        template_name = template_map.get(selected_template, "default")

        # Criar config tipada
        laudo_config = LaudoConfig(
            company_name=self.company_entry.get() or "Nome da Empresa",
            cnpj=self.cnpj_entry.get() or "",
            address=self.address_entry.get() or "",
            footer_text=self.footer_entry.get() or "Documento gerado automaticamente por DataMaster Pro",
            header_color="#d48214",
            text_color="#1e293b",
            template_name=template_name,
            tolerance=1.0,
            sign_enabled=False,
            cert_pfx_path="",
            cert_password="",
            cert_alias=""
        )

        self.action_btn.configure(state="disabled")
        
        _extrato_file = self.extrato_file
        _notas_file = self.notas_file
        _output_path = output_path
        _config = laudo_config

        def _execute_func():
            return self.laudos.generate(_extrato_file, _notas_file, _output_path, _config)

        def _on_complete(result):
            self.after(0, lambda: self._show_results(result))

        task_executor.submit(
            execute_func=_execute_func,
            on_complete=_on_complete,
            tool_name="gerador_laudos",
            tool_display_name="Gerador de Laudos Enterprise",
            user_id=self.user_id
        )

    def _generation_worker(self, output_path, config):
        try:
            result = self.laudos.generate(self.extrato_file, self.notas_file, output_path, config)
            self.after(0, lambda: self._show_results(result) if hasattr(self, 'winfo_exists') and self.winfo_exists() else None)
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)) if hasattr(self, 'winfo_exists') and self.winfo_exists() else None)

    def _show_results(self, result):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.action_btn.configure(state="normal")

        try:
            if hasattr(self, 'results_text') and self.results_text.winfo_exists():
                self.results_text.configure(state="normal")
                self.results_text.delete("1.0", "end")
        except Exception:
            pass

        full_result = ""
        if result.success:
            summary = result.summary

            output = f"""LAUDO ENTERPRISE v3.0 GERADO COM SUCESSO
{'='*50}
Arquivo: {result.output_path}

RESUMO:
  Total de Itens: {summary.get('total_items', 0)}
  Conforme: {summary.get('conforme', 0)}
  Pendentes: {summary.get('nao_conforme', 0)}
  Taxa de Conformidade: {summary.get('compliance_rate', 0)}%

  STATUS: {summary.get('status', 'N/A')}

AUDITORIA:
  Hash SHA-256: {result.manifest.get('sha256', 'N/A')[:32]}...
  Tamanho: {result.manifest.get('size_bytes', 'N/A')} bytes
  Assinado: {'Sim' if result.manifest.get('signed') else 'Não'}
"""
            try:
                if hasattr(self, 'results_text') and self.results_text.winfo_exists():
                    self.results_text.insert("1.0", output)
            except Exception:
                pass
            full_result = output

            messagebox.showinfo("Sucesso", f"Laudo Enterprise gerado com sucesso!\n\nStatus: {summary.get('status', 'N/A')}\nTaxa: {summary.get('compliance_rate', 0)}%")
            rows = summary.get('total_items', 0)
            self._finalize_execution({"success": True}, result.output_path, rows,
                                     {"laudos": 1, "items": rows, "manifest": result.manifest})
        else:
            output = f"Erro: {result.error}"
            try:
                if hasattr(self, 'results_text') and self.results_text.winfo_exists():
                    self.results_text.insert("1.0", output)
            except Exception:
                pass
            full_result = output
            self._finalize_execution({"success": False, "error": result.error}, "")
            messagebox.showerror("Erro", result.error or "Erro desconhecido")

        self._last_result_text = full_result

        try:
            if hasattr(self, 'results_text') and self.results_text.winfo_exists():
                self.results_text.configure(state="disabled")
        except Exception:
            pass

    def _show_error(self, error):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro ao gerar laudo: {error}")
        self.execution.fail(error)