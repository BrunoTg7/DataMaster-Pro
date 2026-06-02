"""
SchedulerOverlay - Overlay flutuante de agendamento de tarefas
Painel estreito (200px) no canto direito, altura automática.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.task_scheduler import get_task_scheduler
from src.core.storage.storage_manager import StorageManager

DIAS_SEMANA = [
    "Segunda-feira", "Terça-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"
]
HORAS = [f"{h:02d}" for h in range(24)]
MINUTOS = [f"{m:02d}" for m in range(60)]


class SchedulerOverlay(ctk.CTkFrame):
    def __init__(self, parent, tool_key: str, tool_display_name: str,
                 user_id: str, input_files: list = None):
        super().__init__(parent, fg_color=config.Colors.CARD, corner_radius=8,
                         border_width=1, border_color=config.Colors.BORDER,
                         width=280, height=400)
        self.parent = parent
        self.tool_key = tool_key
        self.tool_display_name = tool_display_name
        self.user_id = user_id
        self.input_files = list(input_files or [])

        self._scheduler = get_task_scheduler()
        if self._scheduler._storage is None:
            self._scheduler._storage = StorageManager()

        self._setup_ui()
        self._on_frequency_change()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=config.Colors.PRIMARY, height=28, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text=f"🕐 Agendar",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, padx=6, pady=4, sticky="w")

        ctk.CTkButton(
            header, text="✕", width=18, height=18,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent", hover_color=config.Colors.ALERT,
            text_color="#ffffff", corner_radius=2,
            command=self.close
        ).grid(row=0, column=1, padx=(0, 4), pady=2)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        body.grid_columnconfigure(0, weight=1)

        p = 8
        opt_kw = {
            "fg_color": config.Colors.CARD,
            "button_color": config.Colors.PRIMARY,
            "button_hover_color": config.Colors.PRIMARY_HOVER,
            "text_color": config.Colors.TEXT_PRIMARY,
            "dropdown_fg_color": config.Colors.CARD,
            "dropdown_text_color": config.Colors.TEXT_PRIMARY,
            "dropdown_hover_color": config.Colors.BORDER,
            "font": ctk.CTkFont(size=10),
        }

        # Frequência
        ctk.CTkLabel(body, text="Frequência",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color=config.Colors.TEXT_PRIMARY
                      ).grid(row=0, column=0, sticky="w", padx=p, pady=(6, 1))

        self.freq_var = ctk.StringVar(value="daily")
        self.freq_menu = ctk.CTkOptionMenu(
            body, values=["Diário", "Semanal", "Mensal", "Cron"],
            variable=self.freq_var, command=self._on_frequency_change,
            width=200, **opt_kw
        )
        self.freq_menu.grid(row=1, column=0, sticky="ew", padx=p, pady=(0, 4))

        # Horário
        ctk.CTkLabel(body, text="Horário",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color=config.Colors.TEXT_PRIMARY
                      ).grid(row=2, column=0, sticky="w", padx=p, pady=(4, 1))

        self.hour_var = ctk.StringVar(value="08")
        self.min_var = ctk.StringVar(value="00")

        clock_frame = ctk.CTkFrame(body, fg_color="transparent")
        clock_frame.grid(row=3, column=0, sticky="w", padx=p, pady=(0, 4))

        self.hour_menu = ctk.CTkOptionMenu(
            clock_frame, values=HORAS, variable=self.hour_var, width=55, **opt_kw
        )
        self.hour_menu.pack(side="left", padx=(0, 2))

        ctk.CTkLabel(clock_frame, text=":", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=config.Colors.TEXT_SECONDARY).pack(side="left", padx=1)

        self.min_menu = ctk.CTkOptionMenu(
            clock_frame, values=MINUTOS, variable=self.min_var, width=55, **opt_kw
        )
        self.min_menu.pack(side="left", padx=(2, 0))

        # Dia da Semana
        self.week_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.week_frame.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        self.week_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.week_frame, text="Dia da Semana",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color=config.Colors.TEXT_PRIMARY
                      ).grid(row=0, column=0, sticky="w", pady=(4, 1), padx=p)

        self.week_var = ctk.StringVar(value="Segunda-feira")
        self.week_menu = ctk.CTkOptionMenu(
            self.week_frame, values=DIAS_SEMANA, variable=self.week_var,
            width=200, **opt_kw
        )
        self.week_menu.grid(row=1, column=0, sticky="ew", padx=p, pady=(0, 2))

        # Dia do Mês
        self.month_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.month_frame.grid(row=5, column=0, sticky="ew", padx=0, pady=0)
        self.month_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.month_frame, text="Dia do Mês",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color=config.Colors.TEXT_PRIMARY
                      ).grid(row=0, column=0, sticky="w", pady=(4, 1), padx=p)

        self.month_var = ctk.StringVar(value="1")
        self.month_menu = ctk.CTkOptionMenu(
            self.month_frame, values=[str(i) for i in range(1, 32)],
            variable=self.month_var, width=60, **opt_kw
        )
        self.month_menu.grid(row=1, column=0, sticky="w", padx=p, pady=(0, 2))

        # Cron
        self.cron_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.cron_frame.grid(row=6, column=0, sticky="ew", padx=0, pady=0)
        self.cron_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.cron_frame, text="Expressão Cron",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color=config.Colors.TEXT_PRIMARY
                      ).grid(row=0, column=0, sticky="w", pady=(4, 1), padx=p)

        self.cron_entry = ctk.CTkEntry(
            self.cron_frame, placeholder_text="ex: 0 9 * * 1",
            font=ctk.CTkFont(size=10),
            fg_color=config.Colors.CARD,
            text_color=config.Colors.TEXT_PRIMARY,
            border_color=config.Colors.BORDER,
        )
        self.cron_entry.grid(row=1, column=0, sticky="ew", padx=p, pady=(0, 2))

        ctk.CTkLabel(self.cron_frame,
                      text="min hora dia mês dia_semana\n0 9 * * 1 = seg 09:00",
                      font=ctk.CTkFont(size=8),
                      text_color=config.Colors.TEXT_SECONDARY, justify="left"
                      ).grid(row=2, column=0, sticky="w", padx=p, pady=(0, 2))

        # Arquivos
        ctk.CTkLabel(body, text="Arquivos",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color=config.Colors.TEXT_PRIMARY
                      ).grid(row=7, column=0, sticky="w", pady=(4, 1), padx=p)

        self.files_frame = ctk.CTkFrame(body, fg_color=config.Colors.CARD, corner_radius=4)
        self.files_frame.grid(row=8, column=0, sticky="ew", padx=p, pady=(0, 2))
        self.files_frame.grid_columnconfigure(0, weight=1)
        self._render_files()

        ctk.CTkButton(body, text="📁 Arquivos", height=24,
                       fg_color="transparent", hover_color=config.Colors.BORDER,
                       border_width=1, border_color=config.Colors.BORDER,
                       text_color=config.Colors.TEXT_PRIMARY,
                       font=ctk.CTkFont(size=10), corner_radius=4,
                       command=self._browse_files
                       ).grid(row=9, column=0, sticky="ew", padx=p, pady=(0, 4))

        # Tarefas agendadas existentes
        ctk.CTkLabel(body, text="Agendamentos Ativos",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color=config.Colors.TEXT_PRIMARY
                      ).grid(row=10, column=0, sticky="w", pady=(6, 1), padx=p)

        self.scheduled_frame = ctk.CTkFrame(body, fg_color=config.Colors.CARD, corner_radius=4)
        self.scheduled_frame.grid(row=11, column=0, sticky="ew", padx=p, pady=(0, 4))
        self.scheduled_frame.grid_columnconfigure(0, weight=1)
        self._render_scheduled()

        # Botões
        btn_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_frame.grid(row=12, column=0, sticky="ew", padx=p, pady=(2, 8))

        ctk.CTkButton(btn_frame, text="Salvar", height=28,
                       fg_color=config.Colors.PRIMARY,
                       hover_color=config.Colors.PRIMARY_HOVER,
                       font=ctk.CTkFont(size=10, weight="bold"),
                       corner_radius=4, command=self._save
                       ).pack(fill="x", pady=(0, 3))

        ctk.CTkButton(btn_frame, text="Cancelar", height=28,
                       fg_color="transparent", border_width=1,
                       border_color=config.Colors.BORDER,
                       text_color=config.Colors.TEXT_PRIMARY,
                       hover_color=config.Colors.BORDER,
                       font=ctk.CTkFont(size=10), corner_radius=4,
                       command=self.close
                       ).pack(fill="x")

    def _render_files(self):
        for w in self.files_frame.winfo_children():
            w.destroy()

        if self.input_files:
            for i, f in enumerate(self.input_files):
                row = ctk.CTkFrame(self.files_frame, fg_color="transparent")
                row.grid(row=i, column=0, sticky="ew", padx=2, pady=1)
                row.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(row, text=f"📄 {os.path.basename(f)}",
                              font=ctk.CTkFont(size=8),
                              text_color=config.Colors.TEXT_SECONDARY
                              ).grid(row=0, column=0, sticky="w", padx=2)
                ctk.CTkButton(row, text="✕", width=16, height=16,
                               font=ctk.CTkFont(size=8, weight="bold"),
                               fg_color="transparent", hover_color=config.Colors.ALERT,
                               text_color=config.Colors.TEXT_SECONDARY, corner_radius=2,
                               command=lambda path=f: self._remove_file(path)
                               ).grid(row=0, column=1, padx=(2, 0))
        else:
            ctk.CTkLabel(self.files_frame, text="Nenhum",
                          font=ctk.CTkFont(size=9),
                          text_color=config.Colors.TEXT_SECONDARY
                          ).grid(row=0, column=0, sticky="w", padx=4, pady=4)

    def _render_scheduled(self):
        for w in self.scheduled_frame.winfo_children():
            w.destroy()

        try:
            tasks = self._scheduler._storage.get_scheduled_tasks(self.user_id)
            mine = [t for t in tasks if t.get("tool_name") == self.tool_key]
        except Exception:
            mine = []

        if mine:
            mine.sort(key=lambda t: t.get("next_run", ""))
            today = datetime.now().date()
            for i, t in enumerate(mine):
                freq = t.get("schedule_frequency", "?")
                icon = {"daily": "📅", "weekly": "📆", "monthly": "📅", "custom_cron": "⏰"}.get(freq, "⏰")
                next_str = ""
                try:
                    dt = datetime.fromisoformat(t["next_run"])
                    if dt.date() == today:
                        next_str = f"Hoje {dt.strftime('%H:%M')}"
                    else:
                        next_str = dt.strftime("%d/%m %H:%M")
                except Exception:
                    next_str = "—"

                lbl = ctk.CTkLabel(
                    self.scheduled_frame,
                    text=f"{icon} {next_str}",
                    font=ctk.CTkFont(size=8),
                    text_color=config.Colors.TEXT_SECONDARY
                )
                lbl.grid(row=i, column=0, sticky="w", padx=4, pady=1)
        else:
            ctk.CTkLabel(self.scheduled_frame, text="Nenhum agendamento",
                          font=ctk.CTkFont(size=9),
                          text_color=config.Colors.TEXT_SECONDARY
                          ).grid(row=0, column=0, sticky="w", padx=4, pady=4)

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Selecionar Arquivos",
            filetypes=[("Excel", "*.xlsx *.xls"), ("CSV", "*.csv"), ("Todos", "*.*")]
        )
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
        self._render_files()

    def _remove_file(self, path):
        if path in self.input_files:
            self.input_files.remove(path)
        self._render_files()

    def _on_frequency_change(self, *args):
        freq = self.freq_var.get()
        is_weekly = freq == "Semanal"
        is_monthly = freq == "Mensal"
        is_cron = freq == "Cron"

        self.week_frame.grid() if is_weekly else self.week_frame.grid_remove()
        self.month_frame.grid() if is_monthly else self.month_frame.grid_remove()
        self.cron_frame.grid() if is_cron else self.cron_frame.grid_remove()

    def _save(self):
        freq_label = self.freq_var.get()

        if freq_label == "Cron":
            cron_expr = self.cron_entry.get().strip()
            if not cron_expr:
                messagebox.showwarning("Validação", "Informe a expressão Cron.", parent=self)
                return
            time_of_day = None
        else:
            time_of_day = f"{self.hour_var.get()}:{self.min_var.get()}"

        freq_map = {
            "Diário": "daily", "Semanal": "weekly",
            "Mensal": "monthly", "Cron": "custom_cron",
        }
        frequency = freq_map[freq_label]
        cron_expr = self.cron_entry.get().strip() if freq_label == "Cron" else None

        dia_semana = None
        dia_mes = None

        if freq_label == "Semanal":
            dia_semana = DIAS_SEMANA.index(self.week_var.get())
        elif freq_label == "Mensal":
            dia_mes = int(self.month_var.get())

        task = self._scheduler.create_task(
            user_id=self.user_id,
            tool_name=self.tool_key,
            tool_action="execute",
            input_files=self.input_files,
            frequency=frequency,
            time_of_day=time_of_day,
            cron_expression=cron_expr,
        )

        if dia_semana is not None:
            task.day_of_week = dia_semana
        if dia_mes is not None:
            task.day_of_month = dia_mes

        self._scheduler._storage.save_scheduled_task(task)

        if not self._scheduler._polling_thread or not self._scheduler._polling_thread.is_alive():
            self._scheduler.start_polling(interval_seconds=60)

        messagebox.showinfo(
            "Agendado",
            f"{self.tool_display_name} agendada!\n"
            f"Frequência: {freq_label}\n"
            f"Próxima execução: {task.next_run}",
            parent=self
        )
        self.close()

    def close(self):
        self.destroy()
