import customtkinter as ctk
from tkinter import messagebox
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.minerador import MineradorEnterprise
from src.gui.components.result_viewer_modal import ResultViewerButton
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper
from src.core.tasks.task_executor import task_executor


class MineradorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.minerador = MineradorEnterprise(
            progress_callback=self._update_progress,
            log_callback=self._log_from_thread,
            max_concurrency=5,
        )
        self.task_helper = TaskHelper("minerador")
        self.execution = ExecutionHelper("minerador", "Minerador de Preços Enterprise", user_id)
        super().__init__(master, "minerador", "Minerador de Preços Enterprise v5.0", on_back, execution_tracker, user_id)
        self.links = []
        self.current_progress = 0
        self.total_progress = 0
        self._last_result_text = ""
        self._check_task_state()

    def _check_task_state(self):
        last_task = self._tool_service.get_last_task_by_tool("minerador")

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

        self.file_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.file_frame.pack(pady=5)

        self.file_label = ctk.CTkLabel(
            self.file_frame,
            text="",
            font=ctk.CTkFont(family="Inter", size=11),
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

    def _clear_input_file(self):
        if hasattr(self, "input_file"):
            delattr(self, "input_file")
        self.file_label.configure(text="")
        self.file_clear_btn.pack_forget()

    def _select_file(self, files=None):
        if files:
            self.input_file = files[0]
            self.file_label.configure(text=f"✓ {os.path.basename(self.input_file)}")
            self.file_clear_btn.pack(side="left", padx=(6, 0))
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
                self.file_clear_btn.pack(side="left", padx=(6, 0))

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
                self.append_log(log_msg)
        except Exception:
            pass

    def _add_log(self, message: str):
        self.append_log(message)

    def _run_mine(self):
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.log_text.pack(padx=20, pady=10)

        self.append_log("🔄 Iniciando...")

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
        max_per_exec = minerador_limit.get("max_per_exec", 15) if plan.lower() == "gratis" else None
        max_total = minerador_limit.get("max_total") if plan.lower() == "gratis" else None

        # ── Calcula saldo mensal restante via execution_tracker + SQLite local ──
        remaining_monthly = None
        if max_total is not None:
            used_lines = 0
            used_lines_ok = False

            # Tentativa 1: execution_tracker.get_user_stats() — fonte primária (Supabase + SQLite)
            if self.execution_tracker and self.user_id:
                try:
                    created_at = None
                    if isinstance(self.user_data, dict):
                        created_at = self.user_data.get("created_at")
                    cycle_start = self.execution_tracker.get_current_cycle_start(created_at)
                    stats = self.execution_tracker.get_user_stats(self.user_id, start_date=cycle_start)
                    tool_stats = stats.get("by_tool", {}).get("minerador", {"lines": 0})
                    used_lines = int(tool_stats.get("lines", 0))
                    used_lines_ok = True
                    self._log_from_thread(f"[Limite] execution_tracker: {used_lines} linhas usadas no ciclo")
                except Exception as e:
                    self._log_from_thread(f"[Limite] execution_tracker falhou: {e}")

            # Tentativa 2: consulta direta ao SQLite local (sem dependência de rede)
            if not used_lines_ok and self.user_id:
                try:
                    from datetime import datetime
                    execs = self._tool_service.storage.get_executions(self.user_id, limit=2000)
                    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    total = 0
                    for ex in execs:
                        try:
                            ex_date = datetime.fromisoformat(ex.get("created_at", ""))
                            if ex_date < month_start:
                                continue
                            if ex.get("tool_name") == "minerador" and ex.get("status", "completed") == "completed":
                                total += int(ex.get("rows_processed", 0))
                        except Exception:
                            continue
                    used_lines = total
                    used_lines_ok = True
                    self._log_from_thread(f"[Limite] SQLite fallback: {used_lines} linhas usadas")
                except Exception as e:
                    self._log_from_thread(f"[Limite] SQLite fallback falhou: {e}")

            if used_lines_ok:
                remaining_monthly = max(0, max_total - used_lines)
                self._log_from_thread(
                    f"[Limite] Saldo mensal: {used_lines} usados / {max_total} total → {remaining_monthly} restantes"
                )
                if remaining_monthly == 0:
                    messagebox.showwarning(
                        "Limite atingido",
                        f"Você já usou todos os {max_total} links disponíveis este mês.\n"
                        "Aguarde a renovação mensal ou faça upgrade para o plano PRO."
                    )
                    self.progress_frame.pack_forget()
                    self.log_text.pack_forget()
                    return
            else:
                # Ambas as fontes falharam: bloqueia por segurança em vez de deixar passar
                self._log_from_thread("[Limite] ⚠ Não foi possível verificar o saldo — execução bloqueada por segurança.")
                messagebox.showerror(
                    "Erro de verificação",
                    "Não foi possível verificar seu saldo mensal.\n"
                    "Verifique sua conexão e tente novamente."
                )
                self.progress_frame.pack_forget()
                self.log_text.pack_forget()
                return

        # Teto efetivo = menor entre limite por execução e saldo mensal restante
        if max_per_exec is not None and remaining_monthly is not None:
            effective_max = min(max_per_exec, remaining_monthly)
        elif remaining_monthly is not None:
            effective_max = remaining_monthly
        elif max_per_exec is not None:
            effective_max = max_per_exec
        else:
            effective_max = None  # sem limite (plano PRO)

        submitted_urls = list(urls)

        def execute():
            miner = Minerador(
                progress_callback=lambda c, t, p: (
                    task_executor.update_progress(g_id, p, f"Processando {c}/{t}"),
                    self.after(0, self._update_progress_ui, c, t, p),
                ),
                log_callback=lambda m: (
                    task_executor.add_log(g_id, m),
                ),
                _p0=config._r1(),
            )

            if has_file and input_file:
                # Extrai URLs do arquivo aqui e passa para mine_from_links com max_successful
                # (evita depender da versão do minerador_v2 em disco ter o parâmetro)
                try:
                    file_urls = miner._extract_urls_from_file(input_file)
                except AttributeError:
                    # Versão antiga do minerador_v2: usa mine_from_file sem max_successful
                    # e trunca a lista antes (comportamento degradado mas sem crash)
                    result = miner.mine_from_file(input_file, max_links=effective_max)
                    return result
                if not file_urls:
                    return {"success": False, "error": "Nenhuma URL encontrada no arquivo"}
                return miner.mine_from_links(file_urls, max_successful=effective_max)

            if not submitted_urls:
                return {"success": False, "error": "Nenhuma URL informada"}

            # Para URLs manuais: passa tudo, o motor para ao atingir a meta de sucessos
            return miner.mine_from_links(submitted_urls, max_successful=effective_max)

        def on_complete(result):
            self.after(0, lambda: self._show_mine_result(result))

        # Avisa o usuário sobre a meta de sucessos aplicada
        if effective_max is not None and not has_file:
            if remaining_monthly is not None and remaining_monthly < (max_per_exec or 9999):
                self.append_log(
                    f"⚠ Saldo mensal: meta de {remaining_monthly} preços confirmados "
                    f"(de {len(submitted_urls)} URLs). Falhas não contam no saldo."
                )
            else:
                self.append_log(
                    f"⚠ Limite por execução: meta de {effective_max} preços confirmados "
                    f"de {len(submitted_urls)} URLs. Falhas não contam."
                )

        # Valida o limite de execuções ANTES de criar a task no executor
        if not self.start_execution():
            self.progress_frame.pack_forget()
            self.log_text.pack_forget()
            return

        g_id, g_err = task_executor.submit(
            tool_name="minerador",
            tool_display_name="Minerador de Preços",
            execute_func=execute,
            on_complete=on_complete,
            user_id=self.user_id,
        )
        if not g_id:
            self.progress_frame.pack_forget()
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
            all_rows = list(result.get("results", []))
            seen_urls = {r.get("url") for r in all_rows}
            for err in result.get("errors", []):
                if err.get("url") not in seen_urls:
                    seen_urls.add(err.get("url"))
                    all_rows.append(err)
            # Ordena pela ordem original: resultados primeiro, depois erros/cancelados
            if all_rows:
                output_path = self._create_output_path("precos_coletados.xlsx")
                if output_path:
                    theme_map = {"Azul Corporativo": "classic_blue", "Verde Esmeralda": "emerald_green", "Laranja Moderno": "modern_orange", "Cinza Minimalista": "slate_gray"}
                    visual_theme = theme_map.get(self.visual_theme_menu.get(), "classic_blue")
                    self.minerador.export_results(all_rows, output_path, visual_theme=visual_theme)

            collected = result.get("collected", 0)
            self._finalize_execution(result, output_path, collected,
                                     {"links": collected, "total": result.get("total", 0)})

            total = result.get("total", 0)
            errors = result.get("errors", [])
            error_count = len(errors) if errors else 0

            cancelled = sum(1 for e in errors if "Cancelado" in str(e.get("error", "")))
            report = f"📊 RELATÓRIO DE MINERAÇÃO\n{'='*40}\n"
            report += f"Total: {total}\nColetados: {collected}\nCancelados: {cancelled}\nErros: {error_count - cancelled}\n\n"

            for res in result.get("results", []):
                report += f"✅ {res.get('titulo', res.get('title', '?'))}\n   R$ {res.get('preco', res.get('price', 0))} - {res['url']}\n\n"

            if errors:
                has_cancelled = any("Cancelado" in str(e.get("error", "")) for e in errors)
                if has_cancelled:
                    report += f"\n⏭️ NÃO PROCESSADOS (meta atingida):\n"
                    for err in errors:
                        if "Cancelado" in str(err.get("error", "")):
                            report += f"- {err['url']}\n"
                non_cancelled = [e for e in errors if "Cancelado" not in str(e.get("error", ""))]
                if non_cancelled:
                    report += f"\n❌ ERROS:\n"
                    for err in non_cancelled:
                        report += f"- {err['url']}: {err['error']}\n"

            self._last_result_text = report

            real_errors = error_count - cancelled
            msg = f"✅ Coleta concluída!\n\n📊 Resultados: {collected}/{total} preços coletados"
            if cancelled > 0:
                msg += f"\n⏭️ {cancelled} não processados (limite atingido)"
            if real_errors > 0:
                msg += f"\n❌ {real_errors} erro(s) durante a mineração"

            messagebox.showinfo("Sucesso", msg)
        else:
            self._finalize_execution(result, "")
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

        self.status_label.configure(text="")

        self.progress_frame.pack_forget()
        self.log_text.pack_forget()

        if result.get("success"):
            self.text_area.delete("1.0", "end")
            self._clear_input_file()