"""
Minerador Page - Captura preços de sites concorrentes
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.minerador.minerador_v2 import Minerador
from src.gui.components.result_viewer_modal import ResultViewerButton


class MineradorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.minerador = Minerador(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread
        )
        super().__init__(master, "minerador", "Minerador de Preços", on_back, execution_tracker, user_id)
        self.links = []
        self.current_progress = 0
        self.total_progress = 0
        self._last_result_text = ""
    
    def _log_from_thread(self, message: str):
        """Chamado de outra thread - Agenda atualização na thread principal"""
        self.after(0, lambda: self._add_log(message))

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            content,
            text="Cole URLs de produtos para capturar preços automaticamente.",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=400
        )
        info.pack(pady=(20, 10))

        input_frame = ctk.CTkFrame(content, fg_color=config.Colors.CARD, corner_radius=12)
        input_frame.pack(fill="x", padx=20, pady=10)

        lbl = ctk.CTkLabel(
            input_frame,
            text="URLs (uma por linha):",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.text_area = ctk.CTkTextbox(
            input_frame,
            width=500,
            height=150,
            font=ctk.CTkFont(size=12)
        )
        self.text_area.pack(padx=20, pady=(0, 15))

        self.drop_frame = self._create_drop_zone(
            content,
            "Selecione arquivo com URLs",
            self._select_file
        )

        self.file_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.file_label.pack(pady=5)

        self.action_btn = self._create_action_button(content, "Iniciar Captura", self._run_mine)

        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=10)

        self.progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_frame.pack_forget()

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.progress_label.pack()

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=400,
            height=8,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(5, 0))

        self.log_text = ctk.CTkTextbox(
            content,
            width=500,
            height=100,
            font=ctk.CTkFont(size=10),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.log_text.pack(padx=20, pady=10)
        self.log_text.pack_forget()

        self.viewer_btn = ResultViewerButton(
            self,
            content,
            lambda: self._last_result_text if hasattr(self, '_last_result_text') else "",
            "👁️ Visualizar Relatório"
        )
        self.viewer_btn.pack(pady=(0, 15))

    def _select_file(self, files=None):
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

    def _update_progress(self, current: int, total: int, percentage: int):
        self.current_progress = current
        self.total_progress = total
        self.after(0, self._update_progress_ui, current, total, percentage)

    def _update_progress_ui(self, current: int, total: int, percentage: int):
        self.progress_bar.set(percentage / 100)
        self.progress_label.configure(text=f"🔍 Processando {current} de {total} ({percentage}%)")
        
        log_msg = f"[{current}/{total}] Processando... ({percentage}%)"
        self.log_text.insert("end", log_msg + "\n")
        self.log_text.see("end")
    
    def _add_log(self, message: str):
        """Adiciona mensagem de log à área de texto"""
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")

    def _run_mine(self):
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.log_text.pack(padx=20, pady=10)
        
        self.log_text.insert("end", "🔄 Iniciando...\n")
        self.log_text.see("end")
        
        self.progress_bar.set(0)
        self.progress_label.configure(text="🔄 Preparando...")
        self.update()

        def run_in_thread():
            # Capturar URLs dentro da thread
            text = self.text_area.get("1.0", "end").strip()
            urls = [line.strip() for line in text.split("\n") if line.strip()] if text else []
            
            try:
                # Verificar limite
                plan = self.user_data.get("plan", "gratis")
                max_links = 10
                if plan.lower() != "gratis":
                    max_links = None
                else:
                    from config import PLAN_LIMITS, PlanType
                    plan_type = PlanType.GRATIS
                    plan_info = PLAN_LIMITS.get(plan_type, {})
                    tool_limits = plan_info.get("tools_limit", {})
                    minerador_limit = tool_limits.get("minerador", {})
                    max_links = minerador_limit.get("max_per_exec", 10)
                
                if hasattr(self, "input_file") and self.input_file:
                    if not self.start_execution():
                        return
                    
                    self.after(0, lambda: self.log_text.insert("end", f"📂 Arquivo: {os.path.basename(self.input_file)}\n"))
                    self.after(0, lambda: self.log_text.see("end"))
                    self.after(0, lambda: self.progress_label.configure(text=f"📂 Processando arquivo: {os.path.basename(self.input_file)}"))
                    result = self.minerador.mine_from_file(self.input_file, max_links=max_links)
                    self.after(0, lambda: self._show_mine_result(result))
                    return

                if not urls:
                    self.after(0, lambda: self.status_label.configure(text="Insira URLs ou selecione um arquivo"))
                    self.after(0, lambda: self.progress_frame.pack_forget())
                    self.after(0, lambda: self.log_text.pack_forget())
                    return

                if max_links and len(urls) > max_links:
                    self.after(0, lambda: self.log_text.insert("end", f"⚠️ Limite de {max_links} links por execução. Processando {max_links} de {len(urls)}\n"))
                    self.after(0, lambda: self.log_text.see("end"))
                    urls = urls[:max_links]

                if not self.start_execution():
                    return
                self.after(0, lambda: self.log_text.insert("end", f"🚀 Iniciando {len(urls)} URLs...\n"))
                self.after(0, lambda: self.log_text.see("end"))
                self.after(0, lambda: self.progress_label.configure(text=f"🚀 Iniciando mineração de {len(urls)} URLs..."))

                result = self.minerador.mine_from_links(urls)
                self.after(0, lambda: self._show_mine_result(result))
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda msg=error_msg: self.log_text.insert("end", f"❌ ERRO: {msg}\n"))
                self.after(0, lambda: self.log_text.see("end"))
                self.after(0, lambda: self.progress_label.configure(text="❌ Erro"))
                self.after(0, lambda msg=error_msg: messagebox.showerror("Erro", msg))

        import threading
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    def _show_mine_result(self, result):
        self.log_text.insert("end", f"📊 Resultado: {result.get('success', False)}\n")
        self.log_text.see("end")
        
        output_path = ""
        if result.get("success"):
            if result.get("results"):
                output_path = self._create_output_path("precos_coletados.xlsx")
                if output_path:
                    self.minerador.export_results(result["results"], output_path)

            status = "completed"
            self.track_execution(output_path, status, rows_processed=0, links_processed=result.get("total", 0))

            collected = result.get("collected", 0)
            total = result.get("total", 0)
            errors = result.get("errors", [])
            error_count = len(errors) if errors else 0
            
            report = f"📊 RELATÓRIO DE MINERAÇÃO\n{'='*40}\n"
            report += f"Total: {total}\nColetados: {collected}\nErros: {error_count}\n\n"
            
            for res in result.get("results", []):
                report += f"✅ {res['title']}\n   R$ {res['price']} - {res['url']}\n\n"
            
            if errors:
                report += f"\n❌ ERROS:\n"
                for err in errors:
                    report += f"- {err['url']}: {err['error']}\n"
            
            self._last_result_text = report

            msg = f"✅ Coleta concluída!\n\n📊 Resultados: {collected}/{total} preços coletados"
            if error_count > 0:
                msg += f"\n⚠️ {error_count} erros durante a mineração"
            
            messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        self.status_label.configure(text="")
        
        self.progress_frame.pack_forget()
        self.log_text.pack_forget()

        if result.get("success"):
            self.text_area.delete("1.0", "end")
            if hasattr(self, "input_file"):
                delattr(self, "input_file")
            self.file_label.configure(text="")