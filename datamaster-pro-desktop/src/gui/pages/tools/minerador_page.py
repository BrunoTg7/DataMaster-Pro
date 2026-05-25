import customtkinter as ctk
from tkinter import messagebox
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.minerador.minerador_v2 import Minerador
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.global_executor import global_executor


class MineradorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.minerador = Minerador(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread,
            scraperapi_key=config.SCRAPERAPI_KEY,
        )
        self.task_helper = TaskHelper("minerador")
        self.execution = ExecutionHelper("minerador", "Minerador de Preços", user_id)
        super().__init__(master, "minerador", "Minerador de Preços", on_back, execution_tracker, user_id)
        self.links = []
        self.current_progress = 0
        self.total_progress = 0
        self._last_result_text = ""
        self._check_task_state()

    def _check_task_state(self):
        from src.core.storage.storage_manager import StorageManager
        storage = StorageManager()
        last_task = storage.get_last_task_by_tool("minerador")

        if not last_task:
            return

        from datetime import datetime, timedelta
        created = last_task.get("created_at", "")
        if created:
            try:
                created_dt = datetime.fromisoformat(created)
                if datetime.now() - created_dt >= timedelta(hours=2):
                    return
            except Exception:
                return

        status = last_task.get("status")

        if status == "running":
            self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
            self.log_text.pack(padx=20, pady=10)
            progress = last_task.get("progress_percent", 0)
            message = last_task.get("progress_message", "Processando...")
            self.progress_bar.set(progress / 100)
            self.progress_label.configure(text=message)
            log_text = last_task.get("log_text", "")
            if log_text:
                self.log_text.insert("end", log_text)
                self.log_text.see("end")
            self.status_label.configure(text="⏳ Tarefa em andamento...")

        elif status == "completed":
            rows = last_task.get("rows_processed", 0)
            self.status_label.configure(text=f"✅ Última execução concluída ({rows} registros)")

    def _log_from_thread(self, message: str):
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

        # Tema Visual da Planilha
        theme_frame = ctk.CTkFrame(content, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(5, 5))

        ctk.CTkLabel(
            theme_frame,
            text="Tema Visual da Planilha (Excel):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(5, 5))

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
                ("Todos os arquivos", "*.*"),
                ("Excel", "*.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("TXT", "*.txt"),
            ])
            if files:
                self.input_file = files[0]
                self.file_label.configure(text=f"✓ {os.path.basename(self.input_file)}")

    def _update_progress(self, current: int, total: int, percentage: int):
        self.current_progress = current
        self.total_progress = total
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.after(0, self._update_progress_ui, current, total, percentage)
        except Exception:
            pass

    def _update_progress_ui(self, current: int, total: int, percentage: int):
        try:
            if not hasattr(self, 'progress_bar') or not self.progress_bar.winfo_exists():
                return
        except Exception:
            return
        self.progress_bar.set(percentage / 100)
        self.progress_label.configure(text=f"🔍 Processando {current} de {total} ({percentage}%)")

        try:
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                log_msg = f"[{current}/{total}] Processando... ({percentage}%)"
                self.log_text.insert("end", log_msg + "\n")
                self.log_text.see("end")
        except Exception:
            pass

    def _add_log(self, message: str):
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

        text = self.text_area.get("1.0", "end").strip()
        urls = [line.strip() for line in text.split("\n") if line.strip()] if text else []

        has_file = hasattr(self, "input_file") and self.input_file
        input_file = self.input_file if has_file else None

        if not has_file and not urls:
            messagebox.showwarning("Aviso", "Insira URLs ou selecione um arquivo")
            self.progress_frame.pack_forget()
            self.log_text.pack_forget()
            return

        plan = self.user_data.get("plan", "gratis")
        from config import PLAN_LIMITS, PlanType
        plan_type = PlanType.GRATIS if plan.lower() == "gratis" else PlanType.PRO
        plan_info = PLAN_LIMITS.get(plan_type, {})
        tool_limits = plan_info.get("tools_limit", {})
        minerador_limit = tool_limits.get("minerador", {})
        max_links = minerador_limit.get("max_per_exec", 15) if plan.lower() == "gratis" else None

        submitted_urls = list(urls)

        def execute():
            miner = Minerador(
                progress_callback=lambda c, t, p: (
                    global_executor.update_progress(g_id, p, f"Processando {c}/{t}"),
                    self.after(0, self._update_progress_ui, c, t, p),
                ),
                log_callback=lambda m: (
                    global_executor.add_log(g_id, m),
                ),
                scraperapi_key=config.SCRAPERAPI_KEY,
            )

            if has_file and input_file:
                return miner.mine_from_file(input_file, max_links=max_links)

            if not submitted_urls:
                return {"success": False, "error": "Nenhuma URL informada"}

            if max_links and len(submitted_urls) > max_links:
                submitted_urls[:] = submitted_urls[:max_links]

            return miner.mine_from_links(submitted_urls)

        def on_complete(result):
            self.after(0, lambda: self._show_mine_result(result))

        g_id, g_err = global_executor.submit(
            tool_name="minerador",
            tool_display_name="Minerador de Preços",
            execute_func=execute,
            on_complete=on_complete,
            user_id=self.user_id,
        )
        if not g_id:
            self.progress_frame.pack_forget()
            return

        if not self.start_execution():
            return

    def _show_mine_result(self, result):
        try:
            if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
                return
        except Exception:
            return

        self.log_text.insert("end", f"📊 Resultado: {result.get('success', False)}\n")
        self.log_text.see("end")

        output_path = ""
        if result.get("success"):
            if result.get("results"):
                output_path = self._create_output_path("precos_coletados.xlsx")
                if output_path:
                    theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
                    visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")
                    self.minerador.export_results(result["results"], output_path, visual_theme=visual_theme)

            collected = result.get("collected", 0)
            self._finalize_execution(result, output_path, collected,
                                     {"links": collected, "total": result.get("total", 0)})

            total = result.get("total", 0)
            errors = result.get("errors", [])
            error_count = len(errors) if errors else 0

            report = f"📊 RELATÓRIO DE MINERAÇÃO\n{'='*40}\n"
            report += f"Total: {total}\nColetados: {collected}\nErros: {error_count}\n\n"

            for res in result.get("results", []):
                report += f"✅ {res.get('titulo', res.get('title', '?'))}\n   R$ {res.get('preco', res.get('price', 0))} - {res['url']}\n\n"

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
            self._finalize_execution(result, "")
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        self.status_label.configure(text="")

        self.progress_frame.pack_forget()
        self.log_text.pack_forget()

        if result.get("success"):
            self.text_area.delete("1.0", "end")
            if hasattr(self, "input_file"):
                delattr(self, "input_file")
            self.file_label.configure(text="")
