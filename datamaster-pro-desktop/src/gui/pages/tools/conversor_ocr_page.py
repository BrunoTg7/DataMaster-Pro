"""
Conversor OCR Page - Extrai dados de PDFs e Imagens
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.conversor_ocr.conversor_ocr_v2 import ConversorOCR
from src.gui.components.result_viewer_modal import ResultViewerButton


class ConversorOCRPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.ocr = None # Inicializa como None para evitar erro no _create_content
        super().__init__(master, "conversor_ocr", "Conversor OCR Premium", on_back, execution_tracker, user_id)
        self.ocr = ConversorOCR(log_callback=self._log_msg)
        self.input_files = []
        self._last_result_text = ""
        
        # Inicia a verificação e instalação automática sem botão
        self._auto_setup_tesseract()

    def _log_msg(self, msg: str):
        self.after(0, lambda: self._update_results_text(f"> {msg}\n"))

    def _update_results_text(self, text: str):
        self.results_text.configure(state="normal")
        self.results_text.insert("end", text)
        self.results_text.see("end")
        self.results_text.configure(state="disabled")

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        # Status & Tesseract Warning (Oculto se tudo ok)
        self.status_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=20, pady=(10, 0))

        # Drop Zone (Centralizado e Grande)
        self.drop_zone = self._create_drop_zone(
            content, 
            "Arraste seus PDFs ou Imagens aqui", 
            self._on_files_selected
        )

        # Botão de Ação (Abaixo do drop zone, mas integrado)
        self.action_btn = self._create_action_button(content, "Iniciar Conversão para Excel", self._run_conversion)
        self.action_btn.configure(state="disabled") # Só habilita com arquivos

        # Progresso
        self.progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=40, pady=(0, 10))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=10)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        self.progress_frame.pack_forget()

        # Resultados
        results_container = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        results_container.pack(fill="both", expand=True, padx=40, pady=10)
        
        ctk.CTkLabel(
            results_container, 
            text="Log de Processamento:", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(anchor="w", padx=20, pady=(15, 5))

        self.results_text = ctk.CTkTextbox(
            results_container, 
            height=200,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1a1a1a",
            text_color="#d1d5db"
        )
        self.results_text.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.results_text.insert("1.0", "Aguardando arquivos...\n")
        self.results_text.configure(state="disabled")

        self.viewer_btn = ResultViewerButton(
            self,
            content,
            lambda: self._last_result_text if hasattr(self, '_last_result_text') else "",
            "👁️ Visualizar Log Completo"
        )
        self.viewer_btn.pack(pady=(0, 15))

    def _auto_setup_tesseract(self):
        status = self.ocr.get_status()
        tesseract_ok = status.get("tesseract_installed", False)
        
        if not tesseract_ok:
            self._update_results_text("> Configurando motor de OCR automaticamente...\n")
            threading.Thread(target=self._run_silent_setup, daemon=True).start()
        else:
            self._update_results_text("> Motor de OCR pronto.\n")

    def _run_silent_setup(self):
        # 1. Download
        dl_res = self.ocr.download_tesseract()
        if not dl_res["success"]:
            self.after(0, lambda: self._update_results_text(f"❌ Erro ao baixar motor: {dl_res['error']}\n"))
            return
        
        # 2. Silent Install
        inst_res = self.ocr.install_tesseract_silently(dl_res["installer_path"], dl_res["target_dir"])
        
        if inst_res["success"]:
            self.after(0, lambda: self._update_results_text("> Motor de OCR configurado com sucesso!\n"))
        else:
            self.after(0, lambda: self._update_results_text(f"❌ Erro na instalação: {inst_res['error']}\n"))

    def _on_files_selected(self, files=None):
        if not files:
            files = self._browse_files([
                ("Arquivos Suportados", "*.pdf *.png *.jpg *.jpeg *.bmp"),
                ("PDFs", "*.pdf"),
                ("Imagens", "*.png *.jpg *.jpeg *.bmp")
            ])
        
        if files:
            self.input_files = list(files)
            self.action_btn.configure(state="normal")
            
            self.results_text.configure(state="normal")
            self.results_text.delete("1.0", "end")
            self.results_text.insert("end", f"Files loaded: {len(files)}\n")
            for f in files[:10]:
                self.results_text.insert("end", f"- {os.path.basename(f)}\n")
            self.results_text.configure(state="disabled")

    def _run_conversion(self):
        if not self.input_files:
            return

        # Verifica se o OCR está pronto antes de começar
        status = self.ocr.get_status()
        if not status.get("tesseract_installed"):
            messagebox.showwarning("Aguarde", "O motor de OCR ainda está sendo configurado. Aguarde alguns segundos.")
            return

        output_dir = self._browse_folder()
        if not output_dir:
            return

        self.action_btn.configure(state="disabled")
        self.progress_frame.pack(fill="x", padx=40, pady=(0, 10))
        self.progress_bar.set(0)

        # Usar o callback do ConversorOCR para atualizar progresso
        self.ocr.progress_callback = lambda p: self.after(0, lambda: self.progress_bar.set(p/100))

        thread = threading.Thread(target=self._worker, args=(output_dir,), daemon=True)
        thread.start()

    def _worker(self, output_dir):
        try:
            self.after(0, lambda: self._update_results_text("\n--- Iniciando Processamento ---\n"))
            result = self.ocr.process_multiple(self.input_files, output_dir, True)
            self.after(0, lambda: self._show_result_details(result))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, lambda: self.action_btn.configure(state="normal"))

    def _show_result_details(self, result):
        self.progress_frame.pack_forget()
        
        self.results_text.configure(state="normal")
        self.results_text.insert("end", f"\nConcluído!\n")
        self.results_text.insert("end", f"Total: {result.get('total', 0)} | Sucesso: {result.get('processed', 0)}\n")
        
        for r in result.get("results", []):
            name = os.path.basename(r["file"])
            if r["result"].get("success"):
                method = r["result"].get("method", "OCR")
                self.results_text.insert("end", f"✅ {name} ({method})\n")
            else:
                self.results_text.insert("end", f"❌ {name}\n   -> {r['result'].get('error', 'Erro')}\n")
        
        self.results_text.see("end")
        self.results_text.configure(state="disabled")
        
        report = f"📄 RELATÓRIO OCR PREMIUM\n{'='*40}\n"
        report += f"Total: {result.get('total', 0)}\nSucesso: {result.get('processed', 0)}\n\n"
        for r in result.get("results", []):
            status = "✅" if r["result"].get("success") else "❌"
            report += f"{status} {os.path.basename(r['file'])}\n"
            if not r["result"].get("success"):
                report += f"   Erro: {r['result'].get('error')}\n"
        
        self._last_result_text = report
        
        messagebox.showinfo("Sucesso", f"Processamento concluído: {result.get('processed')} de {result.get('total')} arquivos.")