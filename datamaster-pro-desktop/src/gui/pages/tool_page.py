"""
ToolPage Base - Classe base para todas as páginas de ferramentas
"""
import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
from tkinterdnd2 import DND_FILES

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

log = logging.getLogger(__name__)


class ToolPage(ctk.CTkFrame):
    def __init__(self, master, tool_key: str, tool_name: str, on_back,
                 execution_tracker=None, user_data=None):
        super().__init__(master, fg_color=config.Colors.BACKGROUND)

        self.tool_key = tool_key
        self.tool_name = tool_name
        self.on_back = on_back
        self.execution_tracker = execution_tracker
        self._scheduler_btn = None
        self._log_queue = []
        self._log_flush_scheduled = False

        # Flexibilidade: user_data pode ser o objeto completo ou apenas o ID (string)
        if isinstance(user_data, str):
            self.user_id = user_data
            self.user_data = {"id": user_data}
        else:
            self.user_data = user_data or {}
            self.user_id = self.user_data.get("id")
        self.uploaded_files = []
        self._start_time = None
        self._active_overlay = None

        # Service layer
        from src.core.services.tool_service import ToolService
        self._tool_service = ToolService()

        # Toast
        from src.gui.components.toast import ToastManager
        self._toast = ToastManager.get_instance(master)

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_content()

    def _create_header(self):
        header = ctk.CTkFrame(self, fg_color=config.Colors.CARD, height=70, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Voltar",
            width=90,
            height=32,
            fg_color="transparent",
            hover_color=config.Colors.BORDER,
            border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Inter", size=13),
            corner_radius=8,
            command=self.on_back
        )
        back_btn.grid(row=0, column=0, padx=30, pady=15)

        title = ctk.CTkLabel(
            header,
            text=self.tool_name,
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        self._history_btn = ctk.CTkButton(
            header, text="📋 Histórico", width=100, height=32,
            fg_color="transparent", hover_color=config.Colors.BORDER,
            border_width=1, border_color="#3498db",
            text_color="#3498db",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            corner_radius=8, command=self._open_history
        )
        self._history_btn.grid(row=0, column=2, padx=(0, 8), pady=15)

        self._scheduler_btn = ctk.CTkButton(
            header, text="🕐 Agendar", width=100, height=32,
            fg_color="transparent", hover_color=config.Colors.BORDER,
            border_width=1, border_color="#d48214",
            text_color="#d48214",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            corner_radius=8, command=self._open_scheduler
        )
        self._scheduler_btn.grid(row=0, column=3, padx=(0, 20), pady=15)

    def _close_active_overlay(self):
        if self._active_overlay and self._active_overlay.winfo_exists():
            try:
                self._active_overlay.destroy()
            except Exception:
                pass
        self._active_overlay = None

    def _open_scheduler(self):
        self._close_active_overlay()
        from src.gui.components.scheduler_modal import SchedulerOverlay
        overlay = SchedulerOverlay(
            parent=self,
            tool_key=self.tool_key,
            tool_display_name=self.tool_name,
            user_id=self.user_id or "",
            input_files=getattr(self, "uploaded_files", []),
        )
        overlay.place(relx=1.0, rely=0.5, anchor="e", x=-80, y=40)
        overlay.lift()
        self._active_overlay = overlay

    def _open_history(self):
        self._close_active_overlay()
        from src.gui.components.history_overlay import HistoryOverlay
        overlay = HistoryOverlay(
            parent=self,
            tool_key=self.tool_key,
            tool_display_name=self.tool_name,
        )
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()
        self._active_overlay = overlay

    def _create_content(self):
        pass

    def _create_drop_zone(self, parent, label: str, callback) -> ctk.CTkFrame:
        """Cria área de drag & drop"""
        drop_frame = ctk.CTkFrame(
            parent,
            fg_color=config.Colors.CARD,
            corner_radius=16,
            border_width=2,
            border_color=config.Colors.BORDER
        )
        drop_frame.pack(fill="both", expand=True, padx=40, pady=20)

        icon = ctk.CTkLabel(
            drop_frame,
            text="📁",
            font=ctk.CTkFont(size=44),
            text_color=config.Colors.PRIMARY
        )
        icon.pack(pady=(30, 10))

        self.drop_label = ctk.CTkLabel(
            drop_frame,
            text=label,
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        self.drop_label.pack(pady=5)

        self.drop_sublabel = ctk.CTkLabel(
            drop_frame,
            text="Clique no botão para selecionar arquivos",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.drop_sublabel.pack(pady=(0, 25))

        self.drop_btn = ctk.CTkButton(
            drop_frame,
            text="Selecionar Arquivos",
            width=220,
            height=40,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            corner_radius=8,
            command=callback
        )
        self.drop_btn.pack(pady=(0, 30))

        # Configurar Drag & Drop usando tkinterdnd2 (apenas se inicializado com sucesso)
        if hasattr(self.master, 'TkdndVersion') and self.master.TkdndVersion:
            try:
                drop_frame.drop_target_register(DND_FILES)
                
                def on_drop(event):
                    data = event.data
                    if data.startswith('{') and data.endswith('}'):
                        data = data[1:-1]
                    
                    import re
                    files = re.findall(r'{.*?} | \S+', data + ' ')
                    files = [f.strip().strip('{}') for f in files if f.strip()]
                    
                    if not files:
                        files = [data.strip('{}')]

                    if hasattr(self, '_on_files_dropped'):
                        self._on_files_dropped(files, callback)
                    else:
                        try:
                            callback(files)
                        except TypeError:
                            callback()

                drop_frame.dnd_bind('<<Drop>>', on_drop)
                self.drop_sublabel.configure(text="Arraste arquivos aqui ou clique no botão")
            except Exception as e:
                log.error("Erro ao registrar Drop Target: %s", e)
                self.drop_sublabel.configure(text="Clique no botão para selecionar arquivos")
        else:
            self.drop_sublabel.configure(text="Clique no botão para selecionar arquivos")

        return drop_frame

    def _create_file_list(self, parent, files: list) -> ctk.CTkFrame:
        """Cria lista de arquivos selecionados"""
        list_frame = ctk.CTkFrame(parent, fg_color="transparent")
        list_frame.pack(fill="x", padx=20, pady=10)

        if files:
            lbl = ctk.CTkLabel(
                list_frame,
                text=f"Arquivos selecionados: {len(files)}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY
            )
            lbl.pack(anchor="w")

            for f in files:
                file_lbl = ctk.CTkLabel(
                    list_frame,
                    text=f"• {os.path.basename(f)}",
                    font=ctk.CTkFont(size=11),
                    text_color=config.Colors.TEXT_SECONDARY
                )
                file_lbl.pack(anchor="w", padx=10, pady=2)

        return list_frame

    def _create_action_button(self, parent, text: str, callback) -> ctk.CTkButton:
        """Cria botão de ação principal"""
        btn = ctk.CTkButton(
            parent,
            text=text,
            width=240,
            height=45,
            fg_color=config.Colors.PRIMARY,
            hover_color=config.Colors.PRIMARY_HOVER,
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            corner_radius=8,
            command=callback
        )
        btn.pack(pady=30)
        return btn

    def _create_output_path(self, default_name: str) -> str:
        """Solicita caminho de saída"""
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")]
        )
        return output_path

    def _show_result(self, result: dict):
        """Mostra resultado da operação"""
        if result.get("success"):
            messagebox.showinfo(
                "Sucesso",
                f"Operação concluída!\n\n{self._format_result(result)}"
            )
        else:
            messagebox.showerror("Erro", result.get("error", "Erro desconhecido"))

    def _format_result(self, result: dict) -> str:
        """Formata mensagem de resultado"""
        lines = []
        for key, value in result.items():
            if key != "success" and key != "error":
                lines.append(f"{key}: {value}")
        return "\n".join(lines) if lines else "Concluído"

    def start_execution(self, rows_to_process: int = 0) -> int:
        """
        Verifica limites e marca início da execução
        Returns: Quantidade de linhas permitidas (0 se cancelado)
        """
        if self.execution_tracker and self.user_id:
            plan = self.user_data.get("plan", "gratis")
            check = self.execution_tracker.check_limit(
                user_id=self.user_id, 
                plan_name=plan, 
                tool_key=self.tool_key,
                rows_to_process=rows_to_process
            )
            if not check.get("allowed"):
                # Se o erro for por excesso de linhas, oferecemos truncar
                max_total = (600 if self.tool_key != "orcamentos" else 15)
                if rows_to_process > max_total:
                    msg = f"Este arquivo possui {rows_to_process} itens, mas seu plano {plan.upper()} permite apenas {max_total} nesta ferramenta.\n\nDeseja processar apenas os primeiros {max_total}?"
                    if messagebox.askyesno("Limite Excedido", msg):
                        rows_to_process = max_total
                    else:
                        return 0
                else:
                    messagebox.showwarning("Limite Atingido", check.get("error"))
                    return 0

        import time
        self._start_time = time.time()
        # Se rows_to_process é 0 mas allowed=True, retorna 1 para permitir execução
        return rows_to_process if rows_to_process > 0 else 1

    def track_execution(self, output_path: str, status: str = "completed", rows_processed: int = 0, hours_saved: float = None, duration_ms: int = None, links_processed: int = None):
        """Rastreia a execução da ferramenta"""
        if not self.execution_tracker or not self.user_id:
            return

        import time
        if duration_ms is None:
            duration_ms = int((time.time() - self._start_time) * 1000) if self._start_time else 0
        
        # Para minerador, usar links_processed em vez de rows_processed
        actual_rows = rows_processed
        if self.tool_key == "minerador" and links_processed is not None:
            actual_rows = links_processed
        
        # Calcular ROI estimado se não fornecido
        # Média: 30 segundos economizados por linha processada
        if hours_saved is None:
            hours_saved = (actual_rows * 30) / 3600

        self.execution_tracker.track_execution(
            tool_name=self.tool_key,
            user_id=self.user_id,
            input_files=self.uploaded_files if hasattr(self, 'uploaded_files') else [],
            output_path=output_path or "",
            status=status,
            duration_ms=duration_ms,
            rows_processed=actual_rows,
            hours_saved=hours_saved
        )

    def _finalize_execution(self, result, output_path="", rows=0, extra=None, generated_files=None):
        status = "completed" if result.get("success") else "failed"
        log.info("Finalizando %s: status=%s, rows=%s, output=%s", self.tool_key, status, rows, output_path)
        if rows:
            self.track_execution(output_path, status, rows)
            try:
                self._tool_service.storage.save_execution(
                    self.user_id or "offline",
                    self.tool_key,
                    self.uploaded_files if hasattr(self, 'uploaded_files') else [],
                    output_path or "",
                    rows,
                    (rows * 30) / 3600
                )
            except Exception:
                import traceback
                traceback.print_exc()
        if result.get("success") and hasattr(self, 'execution'):
            try:
                tasks = self._tool_service.get_tasks()
                candidates = [t for t in tasks
                              if t.get("tool_name") == self.tool_key and t.get("status") == "completed"]
                if candidates:
                    candidates.sort(key=lambda t: t.get("completed_at") or "", reverse=True)
                    self.execution.task_id = candidates[0]["id"]
                    files = generated_files if generated_files is not None else ([output_path] if output_path else [])
                    self.execution.save_to_history(
                        status="completed",
                        result_data=extra or {},
                        generated_files=files,
                    )
                    log.info("Histórico salvo: %s, task=%s..., %d arquivo(s)", self.tool_key, candidates[0]["id"][:8], len(files))
            except Exception:
                log.exception("Erro ao salvar histórico")
        if result.get("success"):
            self._toast.success(f"{self.tool_name} concluído! {rows} linhas processadas")
        else:
            err_msg = result.get("error", "Erro desconhecido")
            log.error("%s falhou: %s", self.tool_key, err_msg)
            self._toast.error(f"Erro em {self.tool_name}: {err_msg}")
            from tkinter import messagebox
            messagebox.showerror("Erro", err_msg)

    def _browse_files(self, filetypes=None) -> list:
        """Abre diálogo para selecionar arquivos"""
        if filetypes is None:
            filetypes = [
                ("Todos os arquivos", "*"),
                ("Excel", "*.xlsx;*.xls"),
                ("CSV", "*.csv"),
            ]

        files = filedialog.askopenfilenames(filetypes=filetypes)
        return list(files)

    def _browse_folder(self) -> str:
        """Abre diálogo para selecionar pasta"""
        folder = filedialog.askdirectory()
        return folder

    def append_log(self, message: str):
        """Buffer de Progressão e Log (FIFO) - Atualiza UI sem estagnar o processo"""
        self._log_queue.append(message)
        
        if not self._log_flush_scheduled:
            self._log_flush_scheduled = True
            self.after(200, self._flush_logs)

    def _flush_logs(self):
        self._log_flush_scheduled = False
        if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
            self._log_queue.clear()
            return
            
        if self._log_queue:
            batch = "".join(f"{msg}\n" for msg in self._log_queue)
            self._log_queue.clear()
            
            # Tentar estado normal, não quebra se log_text for editável (no read-only tem q destravar antes)
            try:
                self.log_text.configure(state="normal")
            except Exception:
                pass
            
            self.log_text.insert("end", batch)
            
            # Truncar logs para não explodir memória
            content = self.log_text.get("1.0", "end")
            lines = content.count("\n")
            if lines > 1500:
                self.log_text.delete("1.0", f"{lines - 1500 + 1}.0")
            
            self.log_text.see("end")
            
            try:
                self.log_text.configure(state="disabled")
            except Exception:
                pass
