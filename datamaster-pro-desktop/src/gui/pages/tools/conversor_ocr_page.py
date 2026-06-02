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
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor



class ConversorOCRPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.ocr = None # Inicializa como None para evitar erro no _create_content
        self.execution = ExecutionHelper("conversor_ocr", "Conversor OCR Premium", user_id)
        super().__init__(master, "conversor_ocr", "Conversor OCR Premium", on_back, execution_tracker, user_id)
        self._check_task_state()
        self.ocr = ConversorOCR(log_callback=self._log_msg)
        self.input_files = []
        self._last_result_text = ""
        
        # Inicia a verificação e instalação automática sem botão
        self._auto_setup_tesseract()

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("conversor_ocr")
        
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

        # Tema Visual da Planilha
        theme_frame = ctk.CTkFrame(content, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(5, 5))

        ctk.CTkLabel(
            theme_frame,
            text="Tema Visual da Planilha (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(5, 5))
        
        # Verificar se é usuário FREE
        user_plan = self.user_data.get("plan", "gratis").lower() if self.user_data else "gratis"
        is_free_user = user_plan == "gratis"
        
        if is_free_user:
            # Mostrar aviso para FREE users
            aviso_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
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
            theme_frame,
            values=["Azul Corporativo", "Verde Esmeralda", "Laranja Moderno", "Cinza Minimalista"],
            fg_color=config.Colors.BACKGROUND,
            text_color=config.Colors.TEXT_PRIMARY,
            button_color=config.Colors.PRIMARY,
            button_hover_color=config.Colors.PRIMARY_HOVER
        )
        self.visual_theme_menu.set("Azul Corporativo")
        self.visual_theme_menu.pack(anchor="w", pady=(0, 10))
        
        # Desabilitar menu para FREE users
        if is_free_user:
            self.visual_theme_menu.configure(state="disabled")

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

    def _clear_all_files(self):
        self.input_files = []
        self.action_btn.configure(state="disabled")
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "Aguardando arquivos...\n")
        self.results_text.configure(state="disabled")
        if hasattr(self, 'file_list_frame'):
            self.file_list_frame.destroy()

    def _remove_file_at(self, index):
        if 0 <= index < len(self.input_files):
            del self.input_files[index]
            if not self.input_files:
                self._clear_all_files()
            else:
                self._refresh_file_list()

    def _refresh_file_list(self):
        if hasattr(self, 'file_list_frame') and self.file_list_frame.winfo_exists():
            self.file_list_frame.destroy()
        if not self.input_files:
            return
        self.file_list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_list_frame.place(relx=0.5, rely=0.5, anchor="center")
        header = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=f"📁 {len(self.input_files)} arquivo(s)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="Limpar todos",
            width=90, height=24,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color="#e74c3c",
            text_color="#e74c3c",
            border_width=1, border_color="#e74c3c",
            corner_radius=4,
            command=self._clear_all_files
        ).pack(side="right")
        for i, f in enumerate(self.input_files):
            row = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row,
                text=f"📄 {os.path.basename(f)}",
                font=ctk.CTkFont(size=11),
                text_color=config.Colors.TEXT_SECONDARY
            ).pack(side="left")
            ctk.CTkButton(
                row,
                text="✕",
                width=20, height=18,
                font=ctk.CTkFont(size=8, weight="bold"),
                fg_color="transparent",
                hover_color="#e74c3c",
                text_color="#a0a0a0",
                corner_radius=3,
                command=lambda idx=i: self._remove_file_at(idx)
            ).pack(side="right", padx=(4, 0))

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
            self._refresh_file_list()

    def _run_conversion(self):
        if not self.input_files:
            messagebox.showwarning("Aviso", "Selecione os arquivos PDF ou imagem primeiro")
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
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(0)
        except Exception:
            pass

        def _update_progress_safe(p):
            try:
                if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                    self.after(0, lambda: self.progress_bar.set(p/100))
            except Exception:
                pass
        self.ocr.progress_callback = _update_progress_safe

        _input_files = list(self.input_files)
        _output_dir = output_dir

        theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
        visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")

        def _execute_func():
            return self.ocr.process_multiple(_input_files, _output_dir, True, visual_theme=visual_theme)

        def _on_complete(result):
            self.after(0, lambda: self._show_result_details(result) if hasattr(self, 'winfo_exists') and self.winfo_exists() else None)
            self.after(0, lambda: self.action_btn.configure(state="normal") if hasattr(self, 'action_btn') and self.action_btn.winfo_exists() else None)

        task_executor.submit(
            execute_func=_execute_func,
            on_complete=_on_complete,
            tool_name="conversor_ocr",
            tool_display_name="Conversor OCR Premium"
        )

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
        
        processed = result.get('processed', 0)
        self._finalize_execution(result, "", processed, {"arquivos": processed})
        messagebox.showinfo("Sucesso", f"Processamento concluído: {processed} de {result.get('total')} arquivos.")