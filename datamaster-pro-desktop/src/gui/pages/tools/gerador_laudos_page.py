"""
Gerador de Laudos de Conformidade Page
Gera PDFs profissionais cruzando extratos bancários com notas fiscais
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.gerador_laudos.gerador_laudos_v2 import GeradorLaudos
from src.gui.components.result_viewer_modal import ResultViewerButton


class GeradorLaudosPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.laudos = GeradorLaudos()
        super().__init__(master, "gerador_laudos", "Gerador de Laudos", on_back, execution_tracker, user_id)
        self.extrato_file = None
        self.notas_file = None
        self._last_result_text = ""

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Cruze extratos bancários com notas fiscais e gere um Laudo de Conformidade em PDF.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        input_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl_extrato = ctk.CTkLabel(
            input_frame,
            text="1. Extrato Bancário (CSV/Excel):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_extrato.pack(anchor="w", padx=20, pady=(15, 5))

        self.extrato_btn = ctk.CTkButton(
            input_frame,
            text="Selecionar Extrato",
            command=self._select_extrato,
            fg_color=config.Colors.PRIMARY,
            width=180
        )
        self.extrato_btn.pack(anchor="w", padx=20, pady=(0, 5))

        self.extrato_label = ctk.CTkLabel(
            input_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.extrato_label.pack(anchor="w", padx=20, pady=(0, 15))

        lbl_notas = ctk.CTkLabel(
            input_frame,
            text="2. Notas Fiscais (CSV/Excel):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_notas.pack(anchor="w", padx=20, pady=(5, 5))

        self.notas_btn = ctk.CTkButton(
            input_frame,
            text="Selecionar Notas Fiscais",
            command=self._select_notas,
            fg_color=config.Colors.PRIMARY,
            width=180
        )
        self.notas_btn.pack(anchor="w", padx=20, pady=(0, 5))

        self.notas_label = ctk.CTkLabel(
            input_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.notas_label.pack(anchor="w", padx=20, pady=(0, 15))

        config_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        config_frame.pack(fill="x", padx=20, pady=10)

        lbl_config = ctk.CTkLabel(
            config_frame,
            text="Configurações do Laudo:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        lbl_config.pack(anchor="w", padx=20, pady=(15, 10))

        lbl_company = ctk.CTkLabel(
            config_frame,
            text="Nome da Empresa:",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_company.pack(anchor="w", padx=20, pady=(5, 2))

        self.company_entry = ctk.CTkEntry(
            config_frame,
            width=300,
            placeholder_text="Ex: Minha Empresa Ltda",
            font=ctk.CTkFont(size=11)
        )
        self.company_entry.pack(anchor="w", padx=20, pady=(0, 8))

        lbl_cnpj = ctk.CTkLabel(
            config_frame,
            text="CNPJ:",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_cnpj.pack(anchor="w", padx=20, pady=(5, 2))

        self.cnpj_entry = ctk.CTkEntry(
            config_frame,
            width=200,
            placeholder_text="00.000.000/0001-00",
            font=ctk.CTkFont(size=11)
        )
        self.cnpj_entry.pack(anchor="w", padx=20, pady=(0, 8))

        lbl_address = ctk.CTkLabel(
            config_frame,
            text="Endereço:",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_address.pack(anchor="w", padx=20, pady=(5, 2))

        self.address_entry = ctk.CTkEntry(
            config_frame,
            width=350,
            placeholder_text="Rua Exemplo, 123 - Cidade - UF",
            font=ctk.CTkFont(size=11)
        )
        self.address_entry.pack(anchor="w", padx=20, pady=(0, 8))

        lbl_footer = ctk.CTkLabel(
            config_frame,
            text="Texto do Rodapé:",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl_footer.pack(anchor="w", padx=20, pady=(5, 2))

        self.footer_entry = ctk.CTkEntry(
            config_frame,
            width=400,
            placeholder_text="Documento gerado automaticamente",
            font=ctk.CTkFont(size=11)
        )
        self.footer_entry.pack(anchor="w", padx=20, pady=(0, 15))

        self.action_btn = self._create_action_button(content, "Gerar Laudo PDF", self._run_generation)

        results_label = ctk.CTkLabel(
            content,
            text="Resultado:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        results_label.pack(anchor="w", padx=20, pady=(15, 5))

        self.results_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.results_text = ctk.CTkTextbox(
            self.results_frame,
            width=500,
            height=200,
            font=ctk.CTkFont(size=11)
        )
        self.results_text.pack(padx=20, pady=20, fill="both", expand=True)
        self.results_text.insert("1.0", "Configure o laudo e clique em gerar...\n")
        self.results_text.configure(state="disabled")

        self.viewer_btn = ResultViewerButton(
            self,
            content,
            lambda: self._last_result_text if hasattr(self, '_last_result_text') else "",
            "👁️ Visualizar"
        )
        self.viewer_btn.pack(pady=(0, 15))

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
            self._update_status()

    def _update_status(self):
        status_text = ""
        if self.extrato_file:
            status_text += f"Extrato: {os.path.basename(self.extrato_file)}\n"
        if self.notas_file:
            status_text += f"Notas: {os.path.basename(self.notas_file)}\n"
        
        if status_text:
            self.results_text.configure(state="normal")
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", status_text + "\nPronto para gerar!")
            self.results_text.configure(state="disabled")

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

        config = {
            "company_name": self.company_entry.get() or "Nome da Empresa",
            "cnpj": self.cnpj_entry.get() or "",
            "address": self.address_entry.get() or "",
            "footer_text": self.footer_entry.get() or "",
            "header_color": "#d48214",
            "text_color": "#333333"
        }

        self.action_btn.configure(state="disabled")
        
        thread = threading.Thread(target=self._generation_worker, args=(output_path, config), daemon=True)
        thread.start()

    def _generation_worker(self, output_path, config):
        try:
            result = self.laudos.generate(self.extrato_file, self.notas_file, output_path, config)
            self.after(0, lambda: self._show_results(result))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    def _show_results(self, result):
        self.action_btn.configure(state="normal")

        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")

        full_result = ""
        if result.get("success"):
            summary = result.get("summary", {})

            output = f"""LAUDO GERADO COM SUCESSO
{'='*40}
Arquivo: {result.get('output_path', '')}

RESUMO:
  Total de Itens: {summary.get('total_items', 0)}
  Conforme: {summary.get('conforme', 0)}
  Pendentes: {summary.get('nao_conforme', 0)}
  Taxa de Conformidade: {summary.get('compliance_rate', 0)}%

  STATUS: {summary.get('status', 'N/A')}
"""
            self.results_text.insert("1.0", output)
            full_result = output

            messagebox.showinfo("Sucesso", "Laudo de conformidade gerado com sucesso!")
        else:
            output = f"Erro: {result.get('error', 'Erro desconhecido')}"
            self.results_text.insert("1.0", output)
            full_result = output
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        self._last_result_text = full_result
        
        self.results_text.configure(state="disabled")

    def _show_error(self, error):
        self.action_btn.configure(state="normal")
        messagebox.showerror("Erro", f"Erro ao gerar laudo: {error}")